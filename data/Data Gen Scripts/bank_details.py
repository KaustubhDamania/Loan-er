import bs4, requests
from pprint import pprint
import json
from random import randint, seed
from selenium import webdriver
from time import time,sleep
branch_codes = {}
# with open('bank_data.json') as f:
#     temp = json.load(f)
# temp=temp['bank_data']
# for item in temp:
#     branch = item['bank_branch']
#     branch_code = item['bank_acc_no'][:4]
#     branch_codes[branch]=branch_code

list_to_str = lambda arr: ''.join(arr)
bank_data = []
from selenium.webdriver.firefox.options import Options

options = Options()
options.add_argument("--headless")

def bank_accno_gen(branch):
    global branch_codes
    if branch in branch_codes.keys():
        branch_code = branch_codes[branch]
    else:
        branch_code = [str(randint(0,9)) for i in range(4)]
        branch_code = list_to_str(branch_code)
        branch_codes[branch] = branch_code
    return branch_code + list_to_str([str(randint(0,9)) for i in range(11)])

def list_to_json(arr,file_name):
    temp = {}
    index = file_name.index('.')
    temp[file_name[:index]]=arr
    with open(file_name,'w') as fp:
        json.dump(temp, fp, indent=4)


user = 500
with open('../pan_data.json') as f:
    pan_data = json.load(f)
pan_data = pan_data['pan_data']
while user<1000:
    try:
        init_time = time()
        seed(a=None)
        url = 'https://www.policybazaar.com/ifsc/'
        browser = webdriver.Firefox(executable_path='/home/kaustubhdamania/geckodriver',options=options)
        browser.get(url)
        elems = browser.find_elements_by_class_name('roundedBox')
        arr = []
        for i in range(4):
            lol=elems[i].find_elements_by_tag_name('option')
            # print(i,[a.text for a in lol])
            elem = lol[randint(1,len(lol)-1)]
            arr.append(elem.text)
            # print(arr[-1])
            elem.click()
            sleep(0.25)
        arr.append(browser.find_element_by_class_name('resultElement').find_element_by_tag_name('p').text)
        branch = arr[-2]
        ifsc = arr[-1]
        bank_name = arr[0]
        name = pan_data[user]['name']
        temp = {
            'name': name,
            'ifsc': ifsc,
            'bank_acc_no': bank_accno_gen(branch),
            'bank_name': bank_name,
            'bank_branch': branch
        }
        bank_data.append(temp)
        user += 1
        if user%10==0:
            list_to_json(bank_data, 'bank_data1.json')
        print('Iteration no {}, time taken is {}'.format(user,time()-init_time))
    # print(bank_data)
    except Exception as e:
        print(e)
    finally:
        browser.close()
list_to_json(bank_data,'bank_data1.json')
