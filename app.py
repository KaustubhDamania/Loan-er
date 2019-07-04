from flask import Flask,render_template
from pprint import pprint
import json
import os
import dialogflow
from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField
from wtforms.validators import DataRequired

app = Flask(__name__)
app.config['SECRET_KEY']='5791628bb0b13ce0c676dfde280ba245'

class MessageBox(FlaskForm):
    message = StringField('Message', validators=[DataRequired()])
    submit = SubmitField('Send')

def get_fulfillment_texts(message, language_code, project_id):
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(project_id, "unique")
    print(session)
    if message:
        text_input = dialogflow.types.TextInput(text=message,
                                                language_code=language_code)
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
    if form.validate_on_submit():
        message = form.message.data
        # print('message',message)
        language_code = 'en'
        project_id = os.getenv('DIALOGFLOW_PROJECT_ID')
        fulfillment_msg, fulfillment_text = get_fulfillment_texts(message,
                                                        language_code, project_id)
    print(fulfillment_msg)
    return render_template('tp.html',form=form,a=fulfillment_msg)

if __name__=='__main__':
    app.run(debug=False)
