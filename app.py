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
# r.post(url='http://127.0.0.1:5000/myapi',data='hey').text
# r.post(url='http://127.0.0.1:5000/myapi',data='kaustubh damania').text
# r.post(url='http://127.0.0.1:5000/myapi',data='50000').text
# r.post(url='http://127.0.0.1:5000/myapi',data='5 months').text
# r.post(url='http://127.0.0.1:5000/myapi',data='hey@xyz.com').text
# r.post(url='http://127.0.0.1:5000/myapi',data='my pan is WGLFd3954F').text
app = Flask(__name__)
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY
translator = Translator()
db = firestore.Client()
document_name = token_hex(16)
fields = ['aadhar_no','aadhar_pic1','aadhar_pic2','bank_acc','email','ifsc','loan_amt',
        'loan_duration','name','pan','pan_photo','phone_no']
user_data = {i:None for i in fields}

def pan_check(pan):
    if len(pan)!=10:
        return False
    if not pan[:3].isalpha():
        return False
    if pan[3] not in 'PFCHAT':
        return False
    if pan[4] != user_data['name'].split()[-1][0]:
        return False
    if not pan[5:9].isdigit():
        return False
    if not pan[9].isalpha():
        return False
    return True

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
        new_arr = []
        for item in fulfillment_arr:
            # print('fulfillment_messages',item)
            new_arr.append({
                'text': {
                    'text': [item.text.text[0]]
                }
            })
        print(new_arr)
        # if str(fulfillment_arr[0].text.text[0]) != '':
        #     fulfillment_text = fulfillment_arr[0].text.text[0]
        # else:
        #     fulfillment_text = fulfillment_msg

    return fulfillment_msg, new_arr, response

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

    count=1
    #This jugaad ensures that the POST request sent by Dialogflow is not processed
    if not check:
        check=True
        req = request.get_data() #message received through user's post request
        # req = request.get_json(force=True)
        print(request.files)
        if not request.files:
            message = bytes.decode(req)
        else:
            file = request.files['media']
            print(dir(file))
            # TODO: Upload this image to storage
            file.save(os.path.join(os.getcwd(),'{}_{}.jpg'.format(token_hex(8),count)))
            count+=1
            message = file.filename
        try:
            message = jsonify(message)
            message = json.loads(message.json)['queryResult']['queryText']
        except Exception as e:
            print('Exception: {}'.format(e))
            if not request.files:
                message = bytes.decode(req)
            else:
                message = request.files['media'].filename
            pass
        project_id = os.getenv('DIALOGFLOW_PROJECT_ID')
        language_code = get_language_code(message)

        if language_code == 'hi':
            message = translator.translate(message, src='hi', dest='en').text

        # print('language',language_code,'translated_text',message)

        fulfillment_text, fulfillment_msg, response = get_fulfillment_texts(message, project_id)
        intent_name = response.query_result.intent
        intent = {
            "name": intent_name.name,
            "displayName": intent_name.display_name,
            "isFallback": (intent_name.name=='Default Fallback Intent')
        }
        # intent = {
        #     "name": "projects/cabot-xuhseu/agent/intents/fe84a4dd-e03e-4ebf-a9f2-e872bcfa9282",
        #     "displayName": "Default Fallback Intent",
        #     "isFallback": True
        # }
        intent_name = intent['displayName']
        print('intent_name',intent_name)

        if intent_name=='loan':
            # pprint(dir(response))
            pass
        elif intent_name=='get name':
            print('name is',response.query_result.output_contexts[-1].parameters['name'])
            user_data['name']=response.query_result.output_contexts[-1].parameters['name']

        elif intent_name=='amount-1':
            # TODO: Range check
            print('amount is',int(response.query_result.output_contexts[-1].parameters['amount']))
            user_data['loan_amt']=int(response.query_result.output_contexts[-1].parameters['amount'])

        elif intent_name=='loan period':
            # TODO: Range check
            print('duration is',int(response.query_result.output_contexts[-1].parameters['duration']['amount']))
            user_data['loan_duration']=int(response.query_result.output_contexts[-1].parameters['duration']['amount'])

        elif intent_name=='email':
            print('email is',(response.query_result.output_contexts[-1].parameters['email']))
            user_data['email']=response.query_result.output_contexts[-1].parameters['email']

        elif intent_name=='pan':
            # TODO: DB checks
            user_text = response.query_result.query_text
            pan = response.query_result.output_contexts[-1].parameters['pan']
            if pan=='':
                for word in user_text.split():
                    if pan_check(word):
                        pan = word
                        break
            print('pan is',pan)
            user_data['pan']=pan

        elif intent_name=='PAN pic upload':
            pass
        elif intent_name=='Aadhar number':
            # TODO: DB checks
            print('aadhar is',response.query_result.output_contexts[-1].parameters['aadhar'])
            user_data['aadhar_no']=response.query_result.output_contexts[-1].parameters['aadhar']
        elif intent_name=='Aadhar pic front':
            pass
        elif intent_name=='Aadhar pic back':
            pass
        elif intent_name=='Loan approved - yes':
            pass
        elif intent_name=='Loan approved - no':
            pass
        elif intent_name=='Bank details':
            pass

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
