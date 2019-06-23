from flask import Flask,request,render_template
from pprint import pprint
import json
app = Flask(__name__)

@app.route('/',methods=['GET','POST'])

def post():
    req = request.get_json(silent=True, force=True)
    pprint(req)
    myvar=""
    return render_template('tp.html')# json.dumps({'fulfillmentText':'Welcome to Chatbot nibba!'})


if __name__=='__main__':
    app.run()
