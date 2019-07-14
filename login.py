import urllib.request
import urllib.parse

def sendSMS(apikey, numbers, message):
    data =  urllib.parse.urlencode({'apikey': apikey, 'numbers': numbers,
        'message' : message})
    data = data.encode('utf-8')
    request = urllib.request.Request("https://api.textlocal.in/send/?")
    f = urllib.request.urlopen(request, data)
    fr = f.read()
    return(fr)

#resp =  sendSMS('pIyBJ6pdYX8-bGlGy8HXMOL0FG6RGYRo4jZ6W1A0Qf', '919284621757',
    #'This is your message')
print (resp)
