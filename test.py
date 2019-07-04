from flask import Flask,request
import os
app = Flask(__name__)

def detect_intent_texts(project_id, session_id, text, language_code):
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(project_id, session_id)

    if text:
        text_input = dialogflow.types.TextInput(
            text=text, language_code=language_code)
        query_input = dialogflow.types.QueryInput(text=text_input)
        response = session_client.detect_intent(
            session=session, query_input=query_input)
        # print(response.query_result, str(response.query_result.fulfillment_messages[0].text)=='', response.query_result.fulfillment_messages[0].text=='')
        if str(response.query_result.fulfillment_messages[0].text)!='':
            return str(response.query_result.fulfillment_messages[0].text.text[0]),response.query_result.fulfillment_text
        else:
            return response.query_result.fulfillment_text, response.query_result.fulfillment_text


@app.route('/',methods=['GET','POST'])
def dialogf():
    import dialogflow
    project_id = os.getenv('DIALOGFLOW_PROJECT_ID')
    message = 'hey'
    fulfillment_text, fulfillment_msg = detect_intent_texts(project_id, "unique", message, 'en')
    #print('msg',fulfillment_msg,'txt',fulfillment_text)
    return "Hello World!"

@app.route('/tp',methods=['GET','POST'])
def get():
    req = request.get_data()
	#curl -d "Hello World" -X POST http://f3e3681b.ngrok.io/tp --header "Content-Type:application/text"

    print(req)
    return 'This works!'

@app.route('/dbcheck',methods=['GET','POST'])
def dbcheck():
    import firebase_admin
    from firebase_admin import credentials
    path_json = os.getenv('FIREBASE_CREDENTIALS')
    cred = credentials.Certificate(path_json)
    db_app = firebase_admin.initialize_app(cred, {
        'databaseURL' : 'https://cabot-xuhseu.firebaseio.com'
    })
    # db_app = firebase_admin.initialize_app()

    from firebase_admin import db

    obj = db.reference('aadhar_data')
    try:
        print(obj, len(obj))
    except Exception as e:
        print('Doesnt work that way')

    def search(name):
        for i in range(1000):
            obj = db.reference('aadhar_data/{}'.format(i))
            if obj.get().get('name')==name:
                print(obj.get().get('aadhar_number'))
                break
            print(i)
        # print(obj.get())
    search("Namasri Bhanushali") #107th entry
    return 'Hellow'

@app.route('/lang',methods=['GET','POST'])
def lang():
    from langdetect import detect_langs
    message = 'hi'
    languages = detect_langs(message)
    languages = [language.lang for language in languages]
    return message+' '+str(languages)


if __name__=='__main__':
    app.run(debug=False)
