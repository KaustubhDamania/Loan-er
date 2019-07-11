import requests as r
r.post(url='http://127.0.0.1:5000/myapi',data='hey').text
r.post(url='http://127.0.0.1:5000/myapi',data='Mansey Chattopadhyay').text
r.post(url='http://127.0.0.1:5000/myapi',data='50000').text
r.post(url='http://127.0.0.1:5000/myapi',data='5 months').text
r.post(url='http://127.0.0.1:5000/myapi',data='hey@xyz.com').text
r.post(url='http://127.0.0.1:5000/myapi',data='my pan is EDEFC4062B').text
r.post(url='http://localhost:5000/myapi',files={'media':open('/home/kaustubhdamania/pic.jpg','rb')}).text
r.post(url='http://localhost:5000/myapi',data='my aadhar card is 551389431668').text
r.post(url='http://localhost:5000/myapi',files={'media':open('/home/kaustubhdamania/pic.jpg','rb')}).text
r.post(url='http://localhost:5000/myapi',files={'media':open('/home/kaustubhdamania/pic.jpg','rb')}).text
