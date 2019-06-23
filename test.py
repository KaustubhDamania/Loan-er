from flask import Flask,request
import firebase_admin

app = Flask(__name__)

@app.route('/tp',methods=['GET','POST'])
def get():
    req = request.get_data()
	#curl -d "Hello World" -X POST http://f3e3681b.ngrok.io/tp --header "Content-Type:application/text"

    print(req)
    return 'This works!'

if __name__=='__main__':
    app.run()
