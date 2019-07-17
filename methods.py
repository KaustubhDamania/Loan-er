import dialogflow
from emoji import emojize,demojize
from langdetect import detect_langs
import re
from pprint import pprint
from random import randint
import smtplib
from googletrans import Translator

def pan_check(pan):
    from hello import user_data
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
    translator = Translator()
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

# def get_language(message):
#     from hello import isHindi
#     # global isHindi
#     # if isHindi:
#     #     return 'hi'
#     language_code = 'en'
#     try:
#         languages = detect_langs(message)
#         languages = [item.lang for item in languages]
#         for lang in languages:
#             if lang in ['ne','mr','hi']:
#                 language_code = 'hi'
#                 isHindi = True
#                 break
#     except Exception as e:
#         pass
#     return language_code, isHindi

def calc_emi(amount, duration):
    interest = duration - 2
    from math import ceil
    return ceil(amount*(1+interest/100)/duration)


def upload_pic(pic_name):
    from firebase import firebase
    firebase = firebase.FirebaseApplication('https://cabot-xuhseu.firebaseio.com')
    client = storage.Client()
    bucket = client.get_bucket('cabot-xuhseu.appspot.com')

    # posting to firebase storage
    imageBlob = bucket.blob("/")
    imagePath = os.path.join(os.getcwd(),"{}".format(pic_name))
    imageBlob = bucket.blob(pic_name)
    imageBlob.upload_from_filename(imagePath)
    # return str(imageBlob.generate_signed_url(expiration=timedelta(hours=1),
                                            # method='GET'))

def replace_text(pattern, replacement, fulfillment_msg):
    # pattern = re.compile(r'XXXX')
    pattern = re.compile(pattern)
    indices = [m.span() for m in re.finditer(pattern,fulfillment_msg[0]['text']['text'][0])]
    indices = indices[0]
    first_part = fulfillment_msg[0]['text']['text'][0][:indices[0]]
    latter_part = fulfillment_msg[0]['text']['text'][0][indices[1]:]
    fulfillment_msg[0]['text']['text'][0] = first_part+str(replacement)+latter_part

def get_user_data(response,intent_name,fulfillment_msg):
    from run import filename, db, user_data

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
        credit_ref = db.collection(u'credit_score_data')
        credit_score = randint(0,900)
        try:
            query_result1 = credit_ref.where('pan',u'==',user_data['pan']).get()
            for i in query_result1:
                credit_score = i.to_dict()['credit_score']
        except Exception as e:
            print(e)
        if credit_score < 500:
            loaner = 0
        else:
            loaner = ((credit_score-500)/400)*int(user_data['loan_amt'])

        replace_text(r'XXXX',loaner,fulfillment_msg)
        replace_text(r'YY',user_data['loan_duration'],fulfillment_msg)
        replace_text(r'ZZZZ',calc_emi(user_data['loan_amt'],user_data['loan_duration']),fulfillment_msg)

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
    return user_data
