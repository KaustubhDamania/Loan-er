from flask import Flask,render_template
from pprint import pprint
import json
import os
import dialogflow
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

class MessageBox(FlaskForm):
    message = StringField('Message', validators=[DataRequired()])
    submit = SubmitField('Send')

def get_fulfillment_texts(message, project_id):
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(project_id, "unique")
    print(session)
    if message:
        text_input = dialogflow.types.TextInput(text=message,
                                                language_code='en')
        query_input = dialogflow.types.QueryInput(text=text_input)
        response = session_client.detect_intent(session=session,
                                                query_input=query_input)

    if response:
        fulfillment_msg = response.query_result.fulfillment_text
        fulfillment_arr = response.query_result.fulfillment_messages
        if str(fulfillment_arr[0].text.text[0]) != '':
            fulfillment_text = fulfillment_arr[0].text.text[0]
        else:
            fulfillment_text = fulfillment_msg

    return fulfillment_msg, fulfillment_text


@app.route('/',methods=['GET','POST'])
def get_response():
    form = MessageBox()
    text_input, query_input, response,fulfillment_msg, fulfillment_text = [None]*5
    language_code = 'en'
    if form.validate_on_submit():
        message = form.message.data
        # print('message',message)
        try:
            languages = detect_langs(message)
            languages = [item.lang for item in languages]
            for lang in languages:
                if lang in ['ne','mr','hi']:
                    language_code = 'hi'
                    break
        except Exception as e:
            pass

        if language_code == 'hi':
            message = translator.translate(message, src='hi', dest='en').text
        project_id = os.getenv('DIALOGFLOW_PROJECT_ID')
        fulfillment_msg, fulfillment_text = get_fulfillment_texts(message, project_id)
        print('message',message)
    if language_code == 'hi':
        fulfillment_msg = demojize(fulfillment_msg)
        fulfillment_msg = translator.translate(fulfillment_msg, src='en', dest='hi').text
        # pattern = re.compile(r':(\D)+:')
        pattern = re.compile(r':(.*?):')
        emoji_indices = [m.span() for m in re.finditer(pattern,fulfillment_msg)]
        print('fulfillment_msg',fulfillment_msg)
        print('emoji_indices', emoji_indices)

        # for i,j in emoji_indices:
        while len(emoji_indices)>0:
            i,j = emoji_indices[0]
            print('emoji',fulfillment_msg[i:j],i,j)
            translated_text = translator.translate(fulfillment_msg[i:j], src='hi', dest='en').text
            translated_text = translated_text[0]+translated_text[1:-1].strip().lower()+translated_text[-1]
            print('translated_text',translated_text)
            translated_emoji = emojize(translated_text)
            fulfillment_msg = fulfillment_msg[:i]+translated_emoji+fulfillment_msg[j:]
            emoji_indices = [m.span() for m in re.finditer(pattern,fulfillment_msg)]
            if len(emoji_indices)>0:
                emoji_indices.pop(0)

    print(fulfillment_msg)
    return render_template('tp.html',form=form,a=fulfillment_msg)

if __name__=='__main__':
    app.run(debug=False)
