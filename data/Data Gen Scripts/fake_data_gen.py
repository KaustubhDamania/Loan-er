from faker import Faker
from random import randint
from pprint import pprint
from json import dump
from name_gen import random_name
from googletrans import Translator

fake = Faker()
translator = Translator()
list_to_str = lambda arr: ''.join(arr)
no_of_entries = 1000
pan_data = []
aadhar_data = []
credit_score_data = []
combined_json = {}

def list_to_json(arr,file_name):
    temp = {}
    index = file_name.index('.')
    temp[file_name[:index]]=arr
    with open(file_name,'w') as fp:
        dump(temp, fp, indent=4)
    combined_json[file_name[:index]]=arr


def pan_generator(pan_name):
    first_three_chars = [chr(randint(65,90)) for i in range(3)]
    first_three_chars = list_to_str(first_three_chars)
    fourth_char = 'PFCHAT'[randint(0,5)]
    fifth_char = (pan_name.split())[-1][0]
    next_four_chars = [str(randint(0,9)) for i in range(4)]
    next_four_chars = list_to_str(next_four_chars)
    last_char = chr(randint(65,90))
    return first_three_chars+fourth_char+fifth_char+next_four_chars+last_char

for i in range(no_of_entries):
    name = random_name() # fake.name()
    pan = pan_generator(name)
    yob = randint(1950,2000)
    dob = fake.date()
    dob = str(yob) + dob[dob.index('-'):]
    pan_details = {
        'pan': pan,
        'name': name,
        'dob': dob
    }
    address = translator.translate(Faker('hi-IN').address()).text
    aadhar_number = [str(randint(0,9)) for i in range(12)]
    aadhar_number = list_to_str(aadhar_number)
    aadhar_details = {
        'aadhar_number': aadhar_number,
        'name': name,
        'address': address
    }
    credit_score = randint(300,900)
    credit_score_details = {
        'pan': pan,
        'credit_score': credit_score
    }
    pan_data.append(pan_details)
    aadhar_data.append(aadhar_details)
    credit_score_data.append(credit_score_details)

# pprint(pan_data[:5])
# pprint(credit_score_data[:5])
# pprint(aadhar_data[:5])
list_to_json(pan_data,'../pan_data.json')
list_to_json(aadhar_data,'../aadhar_data.json')
list_to_json(credit_score_data,'../credit_score_data.json')

with open('../combined_data.json','w') as fp:
    dump(combined_json,fp,indent=4)

# TODO: bank table:  name, bank_acc_no, ifsc, bank_name, bank_branch
