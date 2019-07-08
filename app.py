from flask import Flask,render_template,request,jsonify,url_for
from pprint import pprint
import json
import os
import dialogflow
from google.cloud import firestore
from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField
from wtforms.validators import DataRequired
from langdetect import detect_langs
from googletrans import Translator
from emoji import emojize, demojize
import re

app = Flask(__name__)
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY
translator = Translator()
db = firestore.Client()


class MessageBox(FlaskForm):
    message = StringField('Message', validators=[DataRequired()])
    submit = SubmitField('Send')

def get_fulfillment_texts(message, project_id):
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(project_id, "unique")
    if message:
        text_input = dialogflow.types.TextInput(text=message,
                                                language_code='en')
        query_input = dialogflow.types.QueryInput(text=text_input)
        response = session_client.detect_intent(session=session,
                                                query_input=query_input)
        print('RESPONSE')
        pprint(response)

    if response:
        fulfillment_msg = response.query_result.fulfillment_text
        fulfillment_arr = response.query_result.fulfillment_messages
        intent_name = response.query_result.intent
        intent_name = {
            "name": intent_name.name,
            "displayName": intent_name.display_name,
            "isFallback": (intent_name.name=='Default Fallback Intent')
        }
        if str(fulfillment_arr[0].text.text[0]) != '':
            fulfillment_text = fulfillment_arr[0].text.text[0]
        else:
            fulfillment_text = fulfillment_msg

    return fulfillment_msg, fulfillment_text, intent_name

def convert_to_hi(fulfillment_msg):
    fulfillment_msg = demojize(fulfillment_msg)
    fulfillment_msg = translator.translate(fulfillment_msg, src='en', dest='hi').text
    pattern = re.compile(r':(.*?):')
    emoji_indices = [m.span() for m in re.finditer(pattern,fulfillment_msg)]
    # print('fulfillment_msg',fulfillment_msg)
    # print('emoji_indices', emoji_indices)

    # for i,j in emoji_indices:
    while len(emoji_indices)>0:
        i,j = emoji_indices[0]
        # print('emoji',fulfillment_msg[i:j],i,j)
        translated_text = translator.translate(fulfillment_msg[i:j], src='hi', dest='en').text
        translated_text = translated_text[0]+translated_text[1:-1].strip().lower()+translated_text[-1]
        # print('translated_text',translated_text)
        translated_emoji = emojize(translated_text)
        fulfillment_msg = fulfillment_msg[:i]+translated_emoji+fulfillment_msg[j:]
        emoji_indices = [m.span() for m in re.finditer(pattern,fulfillment_msg)]
        # print('emoji_indices',emoji_indices)

    return fulfillment_msg

def get_language_code(message):
    language_code = 'en'
    try:
        languages = detect_langs(message)
        languages = [item.lang for item in languages]
        for lang in languages:
            if lang in ['ne','mr','hi']:
                language_code = 'hi'
                break
    except Exception as e:
        pass
    return language_code

def get_message(user_message):
    return user_message


check=False
@app.route('/myapi', methods=['POST'])
def myapi():
    global check
    import requests
    #This jugaad ensures that the POST request sent by Dialogflow is not processed
    if not check:
        check=True
        req = request.get_data() #message received through user's post request
        # req = request.get_json(force=True)
        message = bytes.decode(req)
        try:
            message = jsonify(message)
            # print('dict',message)
            # print(type(message),dir(message))
            # print(message.json)
            message = json.loads(message.json)['queryResult']['queryText']
        except Exception as e:
            print('Exception: {}'.format(e))
            message = bytes.decode(req)
            pass
        print('message',message)
        project_id = os.getenv('DIALOGFLOW_PROJECT_ID')
        language_code = get_language_code(message)

        if language_code == 'hi':
            message = translator.translate(message, src='hi', dest='en').text

        # print('language',language_code,'translated_text',message)

        fulfillment_text, fulfillment_msg, intent = get_fulfillment_texts(message, project_id)

        if language_code == 'hi':
            fulfillment_msg = convert_to_hi(fulfillment_msg)
            fulfillment_text = convert_to_hi(fulfillment_text)

        # response = {'reply':fulfillment_msg}
        # fulfillment_text, fulfillment_msg = ['Welcome to Hell!']*2
        response = {
            "intent": intent,
            "fulfillmentText": fulfillment_text,
            "fulfillmentMessages": [
                {
                    "text": {
                        "text":[fulfillment_msg]
                    }
                }]
        }
        check=False
        return jsonify(response)

    return jsonify({'reply':'404'})

@app.route('/',methods=['GET','POST'])
def get_response():
    form = MessageBox()
    # text_input, query_input, response,fulfillment_msg, fulfillment_text = [None]*5
    # language_code = 'en'
    fulfillment_msg = None
    if form.validate_on_submit():
        import requests
        message = form.message.data
        print('url',request.url+'myapi')
        print('message',message)
        response = requests.post(url=request.url+'myapi',data=message.encode('utf-8'))
        response = json.loads(response.text)
        fulfillment_msg = response.get('fulfillmentText')
    #     message = get_message(form.message.data)
    #     set_language_code()
    #
    #     if language_code == 'hi':
    #         message = translator.translate(message, src='hi', dest='en').text
    #
    #     project_id = os.getenv('DIALOGFLOW_PROJECT_ID')
    #     fulfillment_msg, fulfillment_text = get_fulfillment_texts(message, project_id)
    #     print('message',message)
    #
    # if language_code == 'hi':
    #     fulfillment_msg = convert_to_hi(fulfillment_msg)

    # print(fulfillment_msg)
    return render_template('tp.html',form=form,a=fulfillment_msg)


if __name__=='__main__':
    app.run(debug=False)
