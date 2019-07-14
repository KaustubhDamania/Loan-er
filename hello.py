from flask import Flask, redirect, url_for, request ,render_template, flash
import urllib.request
import urllib.parse
import random
import os
import smtplib
import imghdr
from email.message import EmailMessage

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
    #apikey = 'pIyBJ6pdYX8-bGlGy8HXMOL0FG6RGYRo4jZ6W1A0Qf'
    numbers = '91' + number

    #send no to db
    print('SMS Sending')
    global otp
    #otp = str(random.randint(1000, 9999))
    print(otp)
    otp = '4151'
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
    return render_template('chat.html')

from flask import Flask,render_template,request,jsonify,url_for
from pprint import pprint
import json
import os
import dialogflow
from secrets import token_hex
from google.cloud import firestore,storage
from langdetect import detect_langs
from googletrans import Translator
from twilio.twiml.messaging_response import MessagingResponse
from emoji import emojize, demojize
from datetime import timedelta
import re

# app = Flask(__name__)
# SECRET_KEY = os.urandom(32)
# app.config['SECRET_KEY'] = SECRET_KEY
translator = Translator()
db = firestore.Client()
document_name = token_hex(16)
fields = ['aadhar_no','aadhar_pic1','aadhar_pic2','bank_acc','email','ifsc','loan_amt',
        'loan_duration','name','pan','pan_photo','phone_no']
user_data = {i:None for i in fields}
isHindi = False

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
        # print('RESPONSE')
        # pprint(response)

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
        print('fulfillment_arr',new_arr)
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

def calc_emi(amount, duration):
    interest = duration - 2
    from math import ceil
    return ceil(amount*(1+interest/100)/duration)


def upload_pic(pic_name):
    from firebase import firebase
    firebase = firebase.FirebaseApplication('https://cabot-xuhseu.firebaseio.com')
    client = storage.Client()
    from secrets import token_hex
    bucket = client.get_bucket('cabot-xuhseu.appspot.com')

    # posting to firebase storage
    imageBlob = bucket.blob("/")
    imagePath = os.path.join(os.getcwd(),"{}".format(pic_name))
    imageBlob = bucket.blob(pic_name)
    imageBlob.upload_from_filename(imagePath)
    # return str(imageBlob.generate_signed_url(expiration=timedelta(hours=1),
                                            # method='GET'))

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

        fulfillment_text, fulfillment_msg, response = get_fulfillment_texts(message, project_id)
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

        if intent_name=='loan':
            # pprint(dir(response))
            pass
        elif intent_name=='get name':
            print('name is',response.query_result.output_contexts[-1].parameters['name'])
            user_data['name']=response.query_result.output_contexts[-1].parameters['name']

        elif intent_name=='amount-1':
            print('amount is',int(response.query_result.output_contexts[-1].parameters['amount']))
            user_data['loan_amt']=int(response.query_result.output_contexts[-1].parameters['amount'])

        elif intent_name=='loan period':
            print('duration is',int(response.query_result.output_contexts[-1].parameters['duration']['amount']))
            user_data['loan_duration']=int(response.query_result.output_contexts[-1].parameters['duration']['amount'])

        elif intent_name=='email':
            print('email is',(response.query_result.output_contexts[-1].parameters['email']))
            user_data['email']=response.query_result.output_contexts[-1].parameters['email']

        elif intent_name=='pan':
            user_text = response.query_result.query_text
            pan = response.query_result.output_contexts[-1].parameters['pan']
            if pan=='':
                for word in user_text.split():
                    if pan_check(word):
                        pan = word
                        break
            print('pan is',pan)
            user_data['pan'] = pan

        elif intent_name=='PAN pic upload':
            # upload_pic(filename)
            user_data['pan_photo'] = filename
            count += 1
            # os.remove(filename)

        elif intent_name=='Aadhar number':
            print('aadhar is',str(int(response.query_result.output_contexts[-1].parameters['aadhar'])))
            user_data['aadhar_no'] = str(int(response.query_result.output_contexts[-1].parameters['aadhar']))

        elif intent_name=='Aadhar pic front':
            # upload_pic(filename)
            user_data['aadhar_pic1'] = filename
            count += 1
            # os.remove(filename)

        elif intent_name=='Aadhar pic back':
            # upload_pic(filename)
            user_data['aadhar_pic2'] = filename
            # os.remove(filename)
            pattern = re.compile(r'XXXX')
            indices = [m.span() for m in re.finditer(pattern,fulfillment_msg[0]['text']['text'][0])]
            indices = indices[0]
            # credit_score = db.collection(u'credit_score_data').document(document_name).get().to_dict().get('credit_score')
            credit_ref = db.collection(u'credit_score_data')
            query_result1 = credit_ref.where('pan',u'==',user_data['pan']).get()
            for i in query_result1:
                credit_score = i.to_dict()['credit_score']
            if credit_score < 500:
                loaner = 0
            else:
                loaner = ((credit_score-500)/400)*int(user_data['loan_amt'])
            first_part = fulfillment_msg[0]['text']['text'][0][:indices[0]]
            latter_part = fulfillment_msg[0]['text']['text'][0][indices[1]:]
            fulfillment_msg[0]['text']['text'][0] = first_part+str(loaner)+latter_part

            pattern = re.compile(r'YY')
            indices = [m.span() for m in re.finditer(pattern,fulfillment_msg[0]['text']['text'][0])]
            indices = indices[0]
            first_part = fulfillment_msg[0]['text']['text'][0][:indices[0]]
            latter_part = fulfillment_msg[0]['text']['text'][0][indices[1]:]
            fulfillment_msg[0]['text']['text'][0] = first_part+str(user_data['loan_duration'])+latter_part
            pattern = re.compile(r'ZZZZ')
            indices = [m.span() for m in re.finditer(pattern,fulfillment_msg[0]['text']['text'][0])]
            indices = indices[0]
            first_part = fulfillment_msg[0]['text']['text'][0][:indices[0]]
            latter_part = fulfillment_msg[0]['text']['text'][0][indices[1]:]
            fulfillment_msg[0]['text']['text'][0] = first_part+str(calc_emi(user_data['loan_amt'],user_data['loan_duration']))+latter_part

        elif intent_name=='Loan approved - yes':
            pass

        elif intent_name=='Loan approved - no':
            pass

        elif intent_name=='Bank details':
            user_text = response.query_result.query_text
            user_text = user_text.split('\n')
            user_data['bank_acc']=user_text[0]
            user_data['ifsc']=user_text[1]
            EMAIL_ADDRESS = "codeadventurebot@gmail.com"
            EMAIL_PASSWORD = "17110667071"
            with smtplib.SMTP('smtp.gmail.com',587) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.ehlo()
                smtp.login(EMAIL_ADDRESS,EMAIL_PASSWORD)
                subject="Congratulations! You have completed the loan process"
                body="blah blah"
                msg=f'Subject:{subject}\n\n{body}'
                smtp.sendmail(EMAIL_ADDRESS,user_data['email'],msg)

        pprint(user_data)
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
    reply,arr,response = get_fulfillment_texts(msg, os.getenv('DIALOGFLOW_PROJECT_ID'))
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

    if intent_name=='loan':
        # pprint(dir(response))
        pass
    elif intent_name=='get name':
        print('name is',response.query_result.output_contexts[-1].parameters['name'])
        user_data['name']=response.query_result.output_contexts[-1].parameters['name']

    elif intent_name=='amount-1':
        print('amount is',int(response.query_result.output_contexts[-1].parameters['amount']))
        user_data['loan_amt']=int(response.query_result.output_contexts[-1].parameters['amount'])

    elif intent_name=='loan period':
        print('duration is',int(response.query_result.output_contexts[-1].parameters['duration']['amount']))
        user_data['loan_duration']=int(response.query_result.output_contexts[-1].parameters['duration']['amount'])

    elif intent_name=='email':
        print('email is',(response.query_result.output_contexts[-1].parameters['email']))
        user_data['email']=response.query_result.output_contexts[-1].parameters['email']

    elif intent_name=='pan':
        user_text = response.query_result.query_text
        pan = response.query_result.output_contexts[-1].parameters['pan']
        if pan=='':
            for word in user_text.split():
                if pan_check(word):
                    pan = word
                    break
        print('pan is',pan)
        user_data['pan'] = pan

    elif intent_name=='PAN pic upload':
        # upload_pic(filename)
        user_data['pan_photo'] = filename
        # count += 1
        # os.remove(filename)

    elif intent_name=='Aadhar number':
        print('aadhar is',str(int(response.query_result.output_contexts[-1].parameters['aadhar'])))
        user_data['aadhar_no'] = str(int(response.query_result.output_contexts[-1].parameters['aadhar']))

    elif intent_name=='Aadhar pic front':
        # upload_pic(filename)
        user_data['aadhar_pic1'] = filename
        # count += 1
        # os.remove(filename)

    elif intent_name=='Aadhar pic back':
        # upload_pic(filename)
        user_data['aadhar_pic2'] = filename
        # os.remove(filename)
        pattern = re.compile(r'XXXX')
        indices = [m.span() for m in re.finditer(pattern,fulfillment_msg[0]['text']['text'][0])]
        indices = indices[0]
        # credit_score = db.collection(u'credit_score_data').document(document_name).get().to_dict().get('credit_score')
        credit_ref = db.collection(u'credit_score_data')
        query_result1 = credit_ref.where('pan',u'==',user_data['pan']).get()
        for i in query_result1:
            credit_score = i.to_dict()['credit_score']
        if credit_score < 500:
            loaner = 0
        else:
            loaner = ((credit_score-500)/400)*int(user_data['loan_amt'])
        first_part = fulfillment_msg[0]['text']['text'][0][:indices[0]]
        latter_part = fulfillment_msg[0]['text']['text'][0][indices[1]:]
        fulfillment_msg[0]['text']['text'][0] = first_part+str(loaner)+latter_part

        pattern = re.compile(r'YY')
        indices = [m.span() for m in re.finditer(pattern,fulfillment_msg[0]['text']['text'][0])]
        indices = indices[0]
        first_part = fulfillment_msg[0]['text']['text'][0][:indices[0]]
        latter_part = fulfillment_msg[0]['text']['text'][0][indices[1]:]
        fulfillment_msg[0]['text']['text'][0] = first_part+str(user_data['loan_duration'])+latter_part
        pattern = re.compile(r'ZZZZ')
        indices = [m.span() for m in re.finditer(pattern,fulfillment_msg[0]['text']['text'][0])]
        indices = indices[0]
        first_part = fulfillment_msg[0]['text']['text'][0][:indices[0]]
        latter_part = fulfillment_msg[0]['text']['text'][0][indices[1]:]
        fulfillment_msg[0]['text']['text'][0] = first_part+str(calc_emi(user_data['loan_amt'],user_data['loan_duration']))+latter_part

    elif intent_name=='Loan approved - yes':
        pass

    elif intent_name=='Loan approved - no':
        pass

    elif intent_name=='Bank details':
        user_text = response.query_result.query_text
        user_text = user_text.split('\n')
        user_data['bank_acc']=user_text[0]
        user_data['ifsc']=user_text[1]
        EMAIL_ADDRESS = "codeadventurebot@gmail.com"
        EMAIL_PASSWORD = "17110667071"
        with smtplib.SMTP('smtp.gmail.com',587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(EMAIL_ADDRESS,EMAIL_PASSWORD)
            subject="Congratulations! You have completed the loan process"
            body="blah blah"
            msg=f'Subject:{subject}\n\n{body}'
            smtp.sendmail(EMAIL_ADDRESS,user_data['email'],msg)

    pprint(user_data)
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
    # resp.message("Hello me")
    return str(resp)

@app.route('/sw.js', methods=['GET'])
def sw():
    return app.send_static_file('serviceworker.js')

@app.route('/manifest.json', methods=['GET'])
def manifest():
    return app.send_static_file('manifest.json')


if __name__ == '__main__':
    app.run(debug = True)
