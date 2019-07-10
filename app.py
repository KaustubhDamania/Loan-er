from flask import Flask,render_template,request,jsonify,url_for
from pprint import pprint
import json
import os
import dialogflow
from secrets import token_hex
from google.cloud import firestore
from langdetect import detect_langs
from googletrans import Translator
from emoji import emojize, demojize
import re

app = Flask(__name__)
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY
translator = Translator()
db = firestore.Client()
document_name = token_hex(16)
fields = ['aadhar','aadhar_pic1','aadhar_pic2','bank_acc','email','ifsc','loan_amt',
        'loan_duration','name','pan','pan_photo','phone_no']
user_data = {i:None for i in fields}

def get_fulfillment_texts(message, project_id):
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(project_id, "unique")
    if message:
        text_input = dialogflow.types.TextInput(text=message,
                                                language_code='en')
        query_input = dialogflow.types.QueryInput(text=text_input)
        response = session_client.detect_intent(session=session,
                                                query_input=query_input)
        # print('RESPONSE')
        # pprint(response)

    if response:
        fulfillment_msg = response.query_result.fulfillment_text
        fulfillment_arr = response.query_result.fulfillment_messages
        new_arr=[]
        for item in fulfillment_arr:
            # print('fulfillment_messages',item)
            new_arr.append({
                'text': {
                    'text': [item.text.text[0]]
                }
            })
        print(new_arr)
        intent_name = response.query_result.intent
        intent = {
            "name": intent_name.name,
            "displayName": intent_name.display_name,
            "isFallback": (intent_name.name=='Default Fallback Intent')
        }
        # if str(fulfillment_arr[0].text.text[0]) != '':
        #     fulfillment_text = fulfillment_arr[0].text.text[0]
        # else:
        #     fulfillment_text = fulfillment_msg

    return fulfillment_msg, new_arr, intent

def convert_to_hi(fulfillment_msg):
    fulfillment_msg = demojize(fulfillment_msg)
    fulfillment_msg = translator.translate(fulfillment_msg, src='en', dest='hi').text
    pattern = re.compile(r':(.*?):')
    emoji_indices = [m.span() for m in re.finditer(pattern,fulfillment_msg)]

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
            message = json.loads(message.json)['queryResult']['queryText']
        except Exception as e:
            print('Exception: {}'.format(e))
            message = bytes.decode(req)
            pass
        project_id = os.getenv('DIALOGFLOW_PROJECT_ID')
        language_code = get_language_code(message)

        if language_code == 'hi':
            message = translator.translate(message, src='hi', dest='en').text

        # print('language',language_code,'translated_text',message)

        fulfillment_text, fulfillment_msg, intent = get_fulfillment_texts(message, project_id)
        intent_name = intent['displayName']
        print('intent_name',intent_name)
        if language_code == 'hi':
            for i in range(len(fulfillment_msg)):
                fulfillment_msg[i]['text']['text'][0] = convert_to_hi(fulfillment_msg[i]['text']['text'][0])
            fulfillment_text = convert_to_hi(fulfillment_text)

        # response = {'reply':fulfillment_msg}
        # fulfillment_text, fulfillment_msg = ['Welcome to Hell!']*2
        response = {
            "intent": intent,
            "fulfillmentText": fulfillment_text,
            "fulfillmentMessages": fulfillment_msg
        }
        check=False
        return jsonify(response)

    return jsonify({'reply':'404'})


if __name__=='__main__':
    app.run()
