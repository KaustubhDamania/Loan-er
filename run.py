from flask import Flask, redirect, url_for, request ,render_template, flash
from flask import jsonify, make_response, send_from_directory, session
import urllib.request
import urllib.parse
import random
import os
import smtplib
from email.message import EmailMessage
from methods import *
from pprint import pprint
import json
import os
import dialogflow
from secrets import token_hex
from google.cloud import firestore,storage
from langdetect import detect_langs
from googletrans import Translator
from random import randint
from twilio.twiml.messaging_response import MessagingResponse
from emoji import emojize, demojize
from datetime import timedelta
import re
from uuid import uuid4

os.environ['GOOGLE_APPLICATION_CREDENTIALS']=os.path.join(os.getcwd(),'CABOT-50ba37921312.json')

app = Flask(__name__)
app.secret_key = 'my unobvious secret key'

otp = '0'
number = '0'

url = "https://www.fast2sms.com/dev/bulk"

headers = {
    'cache-control': "no-cache"
}

#method to send otp
@app.route('/resend-otp')
def sendSMS():
    #apikey = '<Enter your Textlocal API Key>'
    numbers = '91' + number

    #send no to db
    print('SMS Sending')
    global otp
    #otp = str(random.randint(1000, 9999))
    print(otp)
    otp = '4151'    #comment this after adding apikey
    #send otp to the Number
    '''data =  urllib.parse.urlencode({'apikey': apikey, 'numbers': numbers,
        'message' : "Your ABFL OTP is " + otp})
    data = data.encode('utf-8')
    request = urllib.request.Request("https://api.textlocal.in/send/?")
    f = urllib.request.urlopen(request, data)
    fr = f.read()
    print(fr)'''
    return redirect(url_for('get_otp'))

#login page on startup
@app.route('/')
def login():
    return render_template('login.html')

#to trigger the sending of otp to the mobile number typed by the user
@app.route('/login', methods = ['GET', 'POST'])
def send_otp():
    global number
    if request.method == 'POST':
        number = request.form['num']
    sendSMS()
    return redirect(url_for('get_otp'))

#to direct user to enter the otp sent to this phone
@app.route('/enter-otp')
def get_otp():
    return render_template('verify.html')

#to verify the otp typed in by the user
@app.route('/verify', methods = ['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        otp1 = request.form['otp-1']
        otp2 = request.form['otp-2']
        otp3 = request.form['otp-3']
        otp4 = request.form['otp-4']
        otpp = otp1 + otp2 + otp3 + otp4
        # return (otpp + otp)
        if otpp == otp:
            return redirect(url_for('chat_interface'))
        else:
            return redirect(url_for('get_otp'))

#the main chat interface
@app.route('/chat')
def chat_interface():
    session['uid']=str(uuid4())
    print("session['uid']", session['uid'])
    return render_template('chat.html')

translator = Translator()
db = firestore.Client()
document_name = token_hex(16)
fields = ['aadhar_no','aadhar_pic1','aadhar_pic2','bank_acc','email','ifsc','loan_amt',
        'loan_duration','name','pan','pan_photo','phone_no']
user_data = {i:None for i in fields}
isHindi = False
filename = None

def get_language_code(message):
    global isHindi
    # if isHindi:
    #     return 'hi'
    language_code = 'en'
    try:
        languages = detect_langs(message)
        languages = [item.lang for item in languages]
        for lang in languages:
            if lang in ['ne','mr','hi']:
                language_code = 'hi'
                isHindi = True
                break
    except Exception as e:
        pass
    return language_code

check=False
@app.route('/myapi', methods=['POST'])
def myapi():
    global check
    import requests
    key,filename,message='','',''
    count=1

    #This jugaad ensures that the POST request sent by Dialogflow is not processed
    if not check:
        check=True
        req = request.get_data() #message received through user's post request
        # req = request.get_json(force=True)
        print('data',req)
        print(request.files)
        # print(request.headers.get('Content-Type'))
        # print('image' not in request.headers.get('Content-Type'))
        if not request.files:
            message = bytes.decode(req)
        else:
            keys = request.files.keys()
            for i in keys:
                key=i
            file = request.files[key]
            # print(dir(file))
            # TODO: Upload this image to storage
            filename = '{}_{}.jpg'.format(token_hex(8),count)
            file.save(os.path.join(os.getcwd(),filename))
            count += 1
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

        project_id = os.getenv('DIALOGFLOW_PROJECT_ID')
        language_code = get_language_code(message)
        filename = '{}_{}.jpg'.format(token_hex(8),count)
        if language_code == 'hi':
            message = translator.translate(message, src='hi', dest='en').text

        # print('language',language_code,'translated_text',message)

        fulfillment_text, fulfillment_msg, response = get_fulfillment_texts(message, project_id, session['uid'])
        intent_name = response.query_result.intent
        intent = {
            "name": intent_name.name,
            "displayName": intent_name.display_name,
            "isFallback": (intent_name.display_name=='Default Fallback Intent')
        }
        # intent = {
        #     "name": "projects/cabot-xuhseu/agent/intents/fe84a4dd-e03e-4ebf-a9f2-e872bcfa9282",
        #     "displayName": "Default Fallback Intent",
        #     "isFallback": True
        # }
        intent_name = intent['displayName']
        print('intent_name',intent_name)
        print('isHindi',isHindi)

        user_data = get_user_data(response,intent_name,fulfillment_msg)
        if intent_name != 'Default Fallback Intent':
            db.collection('user_data').document(document_name).set(user_data)

        if language_code == 'hi' or isHindi:
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

@app.route("/sms",methods=['POST'])
def sms_reply():
    #re
    msg=request.form.get('Body')
    phoneno=request.form.get('From')
    #mediaurlx=request.form.get('MediaUrlX')
    #print("mediaurlx",mediaurlx)
    num_media = int(request.values.get("NumMedia"))
    for idx in range(num_media):
        media_url = request.values.get(f'MediaUrl{idx}')
        print("urls",media_url)
    print("msg",msg)
    print("phoneno",phoneno)
    if(num_media):
        msg="img.png"    #create reply
    # reply=fetch_reply(msg,phoneno)
    reply,arr,response = get_fulfillment_texts(msg, os.getenv('DIALOGFLOW_PROJECT_ID'), session['uid'])
    intent_name = response.query_result.intent
    intent = {
        "name": intent_name.name,
        "displayName": intent_name.display_name,
        "isFallback": (intent_name.display_name=='Default Fallback Intent')
    }
    fulfillment_msg = arr.copy()
    fulfillment_text = reply
    # intent = {

    #     "name": "projects/cabot-xuhseu/agent/intents/fe84a4dd-e03e-4ebf-a9f2-e872bcfa9282",
    #     "displayName": "Default Fallback Intent",
    #     "isFallback": True
    # }
    intent_name = intent['displayName']
    filename = '{}.jpg'.format(token_hex(8))
    print('intent_name',intent_name)
    print('isHindi',isHindi)

    user_data = get_user_data(response,intent_name,fulfillment_msg)
    if intent_name != 'Default Fallback Intent':
        db.collection('user_data').document(document_name).set(user_data)
    resp=MessagingResponse()
    # resp.message(reply)
    stri = ''
    for r in arr:
        stri += r['text']['text'][0]
        # stri += '\n'
    if(stri=="Okay, based on your credit score, we can give you ₹XXXX amount for YY months with monthly EMI as ₹ZZZZ. Do you approve this loan?"):
        #calc_emi(user_data['loan_amt'],user_data['loan_duration']
        amt=user_data['loan_amt']
        dur=user_data['loan_duration']
        print("amt dur",amt,dur)

    print(stri)
    resp.message(stri)
    return str(resp)

@app.route('/<path:path>')
def send_js(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    app.run(debug = True)
