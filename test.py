from flask import Flask,request,url_for,jsonify,render_template
import os
from pprint import pprint, pformat
from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField
from wtforms.validators import DataRequired
import firebase_admin
from firebase_admin import credentials
app = Flask(__name__)
data_fields = ['mobile_number','name','loan_amt','loan_period','email','pan',
               'pan_front','aadhar_no','aadhar_front','aadhar_back','loan_approved',
               'bank_account_no','ifsc']
intents = [
                'loan',
                'get name',
                ['amount-1','amount-0'],
                'email',
                ['pan incorrect','pan','pan details mismatch'],
                ['PAN pic upload'],
                ['Aadhar number','Aadhar incorrect format','Details mismatch'],
                'Aadhar pic front',
                'Aadhar pic back',
                ['Loan approved - yes', 'Loan approved - no'],
                'Bank details'
           ]
user_data = {i:None for i in data_fields}

class MessageBox(FlaskForm):
    message = StringField('Message', validators=[DataRequired()])
    submit = SubmitField('Send')

def detect_intent_texts(project_id, session_id, text, language_code):
    import dialogflow
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(project_id, session_id)

    if text:
        text_input = dialogflow.types.TextInput(
            text=text, language_code=language_code)
        query_input = dialogflow.types.QueryInput(text=text_input)
        print('text_input',text_input)
        print('query_input',query_input)
        response = session_client.detect_intent(
            session=session, query_input=query_input)
        print('response',response)
        # print(response.query_result, str(response.query_result.fulfillment_messages[0].text)=='', response.query_result.fulfillment_messages[0].text=='')
        if str(response.query_result.fulfillment_messages[0].text)!='':
            return str(response.query_result.fulfillment_messages[0].text.text[0]),response.query_result.fulfillment_text, response
        else:
            return response.query_result.fulfillment_text, response.query_result.fulfillment_text, response

def pan_check(pan):
    if len(pan)!=10:
        return False
    if not pan[:3].isalpha():
        return False
    if pan[3] not in 'PFCHAT':
        return False
    if pan[4] != user_data['name'][0]:
        return False
    if not pan[5:9].isdigit():
        return False
    if not pan[9].isalpha():
        return False
    return True

@app.route('/',methods=['GET','POST'])
def nothing():
    return '<h1>Nothing here!<h1>'

# Route for dialogflow api testing
@app.route('/dialogf',methods=['GET','POST'])
def dialogf():
    project_id = os.getenv('DIALOGFLOW_PROJECT_ID')
    message = request.args['m']
    fulfillment_text, fulfillment_msg, response = detect_intent_texts(project_id, "unique", message, 'en')
    #print('msg',fulfillment_msg,'txt',fulfillment_text)
    pprint(response)
    line_break = "<br>"*2
    intent_name = str(response.query_result.intent.display_name)
    return fulfillment_msg + line_break + str(response) + line_break + intent_name

check=False
@app.route('/myapi', methods=['POST'])
def myapi():
    global check
    import requests
    if not check:
        check=True
        req = request.get_data() #message received through post request
        message = bytes.decode(req)
        print('message',message)
        project_id = os.getenv('DIALOGFLOW_PROJECT_ID')
        fulfillment_text, fulfillment_msg, response = detect_intent_texts(project_id, "unique", message, 'en')
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
        return jsonify(response)
    return jsonify({'reply':''})

# Route for language detection
@app.route('/lang',methods=['GET','POST'])
def lang():
    from langdetect import detect_langs
    message = 'hi'
    languages = detect_langs(message)
    languages = [language.lang for language in languages]
    return message+' '+str(languages)

# Route for firebase firestore
@app.route('/store',methods=['GET','POST'])
def store():
    from google.cloud import firestore
    fire = firestore.Client()
    aadhar_ref = fire.collection(u'aadhar_data')

    #Push some data
    # aadhar_ref.document(u'tp').set({'a':1,'b':2})

    # Get some data
    print(aadhar_ref.document(u'0').get().to_dict())
    from random import randint
    for i in range(50):
        print(fire.collection(u'pan_data').document(str(randint(0,999))).get().to_dict().get('pan'))


    # Query data
    from time import time
    init_time = time()
    query_result1 = aadhar_ref.where('aadhar_number',u'==',u'033878102619').get()
    time_taken = time()-init_time
    print('time_taken #1', time_taken)
    for documents in query_result1:
        print(documents.to_dict(), documents.id)

    query_result2 = aadhar_ref.where('aadhar_number',u'>',u'0').get() #Worst Case
    time_taken = time()-init_time
    print('time_taken #2', time_taken)

    for documents in query_result2: #large output
        print(documents.to_dict(), documents.id)
    return 'Some'

# Route for firebase realtime database
# @app.route('/dbcheck',methods=['GET','POST'])
# def dbcheck():
#     path_json = os.getenv('FIREBASE_CREDENTIALS')
#     cred = credentials.Certificate(path_json)
#     db_app = firebase_admin.initialize_app(cred, {
#         'databaseURL' : 'https://cabot-xuhseu.firebaseio.com'
#     })
#     # db_app = firebase_admin.initialize_app()
#
#     from firebase_admin import db
#
#     obj = db.reference('aadhar_data')
#     try:
#         print(obj, len(obj))
#     except Exception as e:
#         print('Doesnt work that way')
#
#     def search(name):
#         for i in range(1000):
#             obj = db.reference('aadhar_data/{}'.format(i))
#             if obj.get().get('name')==name:
#                 print(obj.get().get('aadhar_number'))
#                 break
#             print(i)
#         # print(obj.get())
#     search("Namasri Bhanushali") #107th entry
#     return 'Hellow'

# Route for trying request library
@app.route('/tp',methods=['GET'])
def get():
    # req = request.get_data()
    req = request.args['name']
	# curl -d "Hello World" -X POST http://f3e3681b.ngrok.io/tp --header "Content-Type:application/text"
    # bytes.decode(req)
    print(req)
    return 'This works!'+'<br>'+str(req)

@app.route('/frontend',methods=['GET','POST'])
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
    return render_template('tp.html',form=form,a=fulfillment_msg)

@app.route('/storages',methods=['GET','POST'])
def storages():
    # from google.cloud import storage
    from google.cloud import storage
    from firebase import firebase
    import os

    # os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="<add your credentials path>"
    firebase = firebase.FirebaseApplication('https://cabot-xuhseu.firebaseio.com')
    client = storage.Client()
    from secrets import token_hex
    bucket = client.get_bucket('cabot-xuhseu.appspot.com')

    # posting to firebase storage

    imageBlob = bucket.blob("/")

    # imagePath = [os.path.join(self.path,f) for f in os.listdir(self.path)]
    imagePath = "/home/kaustubhdamania/pic.jpg"
    imageBlob = bucket.blob("pic.jpg")
    imageBlob.upload_from_filename(imagePath)
    from datetime import timedelta
    return 'It works!'+'<br>'+str(imageBlob.generate_signed_url(expiration=timedelta(hours=1),method='GET'))

if __name__=='__main__':
    app.run()
