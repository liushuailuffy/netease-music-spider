# coding = utf-8
from Crypto.Cipher import AES
import base64
import requests
import json
import time
import random
import threading

import Config
import music_mysql
import IPProxymaster.Util

xsum = 0 #检测的总评论数
lock = threading.Lock() #线程锁
if_beyond_limit_date = False #是否超出规定的限制时间标志

# headers
headers = {
    'Referer': 'http://music.163.com/',
    'User-Agent': random.choice(Config.UserAgents)
}

#代理
myproxies = {
    'http:':'http://180.123.225.51',
    'https:':'https://111.72.126.116'
}
#获取代理ip列表
result = IPProxymaster.Util.GetIPList()
#随机获取代理
def get_random_proxies():
    proxies_dict = {}
    if result:
        tmp = random.choice(result)
        proxies_dict['http:'] = 'http://{}'.format(tmp)
        proxies_dict['https:'] = 'https://{}'.format(tmp)
    return proxies_dict
    

#获取params
def get_params(first_param, forth_param):
    iv = "0102030405060708"
    first_key = forth_param
    second_key = 16 * 'F'
    h_encText = AES_encrypt(first_param, first_key.encode(), iv.encode())
    h_encText = AES_encrypt(h_encText.decode(), second_key.encode(), iv.encode())
    return h_encText.decode()


# 获取encSecKey
def get_encSecKey():
    encSecKey = "257348aecb5e556c066de214e531faadd1c55d814f9be95fd06d6bff9f4c7a41f831f6394d5a3fd2e3881736d94a02ca919d952872e7d0a50ebfa1769a7a62d512f5f1ca21aec60bc3819a9c3ffca5eca9a0dba6d6f7249b06f5965ecfff3695b54e1c28f3f624750ed39e7de08fc8493242e26dbc4484a01c76f739e135637c"
    return encSecKey


# 解AES秘
def AES_encrypt(text, key, iv):
    pad = 16 - len(text) % 16
    text = text + pad * chr(pad)
    encryptor = AES.new(key, AES.MODE_CBC, iv)
    encrypt_text = encryptor.encrypt(text.encode())
    encrypt_text = base64.b64encode(encrypt_text)
    return encrypt_text


# 获取json数据
def get_json(url, data):
    response = requests.post(url,
                             timeout=20,
                             data=data,
                             proxies=get_random_proxies(),
                             headers = {
                                 'Referer': 'http://music.163.com/',
                                 'User-Agent': random.choice(Config.UserAgents)
                                 #'User-Agent': 'Baiduspider'
                                 }
                             )
    return response.content

# 传入post数据
def crypt_api(id, offset):
    url = "http://music.163.com/weapi/v1/resource/comments/R_SO_4_%s/?csrf_token=" % id
    first_param = "{rid:\"\", offset:\"%s\", total:\"true\", limit:\"20\", csrf_token:\"\"}" % offset
    forth_param = "0CoJUm6Qyw8W8jud"
    params = get_params(first_param, forth_param)
    encSecKey = get_encSecKey()
    data = {
        "params": params,
        "encSecKey": encSecKey
    }
    return url, data

#把获取到的用户评论信息插入数据库
def insert_user_comment():
    pass

# 获取评论
def get_comment(id):
    print('**********************开始检查id为',id,'的歌')
    try:
        offset = 0
        url, data = crypt_api(id, offset)
        json_text = get_json(url, data)
        json_dict = json.loads(json_text.decode("utf-8"))
        comments_sum = json_dict['total']
        print("歌曲评论总数为：",comments_sum)
        for i in range(0, comments_sum, Config.MaxThreads*20):
            for index in range(0, Config.MaxThreads):
                offset = i + index*20
                print(index,"号线程开始。评论偏移量为",offset)
                t = threading.Thread(target=thread_get_comment,args=(id,offset,))
                t.start()
                t.join()
                print(index,"号线程结束。评论偏移量为",offset)
            time.sleep(1)
        print('********************id=',id,'的歌检查结束')
    except Exception as e:
        print('出现错误啦~错误是:', e)
        pass

def thread_get_comment(id,offset):
    global xsum
    global result
    mon = 0
    day = 0
    print("进入线程offset为：",offset)
    try:
        url, data = crypt_api(id, offset)
        json_text = get_json(url, data)
        json_dict = json.loads(json_text.decode("utf-8"))
        json_comment = json_dict['comments']
        for json_comment in json_comment:
            user_id = json_comment['user']['userId']
            user_name = json_comment['user']['nickname']
            comment_time = json_comment['time']
            comment = json_comment['content']
            trs_time = time.localtime(comment_time*0.001)
            year = trs_time.tm_year
            mon = trs_time.tm_mon
            day = trs_time.tm_mday
            limit_date = Config.Date
            get_date = str(year)+'-'+str(mon)+'-'+str(day)
            trs_limit_date = time.mktime(time.strptime(limit_date,'%Y-%m-%d'))
            trs_get_date = time.mktime(time.strptime(get_date,'%Y-%m-%d'))
            print(trs_limit_date,trs_get_date)
            #只获取Date之后的评论
            if trs_get_date < trs_limit_date:
                break
            # 添加评论的ID，名字以及评论到数据库中
            if user_id==Config.TestId or user_id==Config.TestId2:
                hour = trs_time.tm_hour
                minute = trs_time.tm_min
                sec = trs_time.tm_sec
                date = str(year)+'-'+str(mon)+'-'+str(day)+' '+str(hour)+':'+str(minute)+':'+str(sec)
                music_mysql.insert_commnet(user_id, user_name, comment,date,id)
                #print('time = ',trs_time.tm_year,'-',trs_time.tm_mon,'-',trs_time.tm_mday, end=" ")
                print('id = ',user_id,user_name,'已经添加到user_comment数据库中啦')
        lock.acquire()
        xsum = xsum + 20
        print('已检查',xsum,'个评论,时间为',year,mon,day)
        lock.release()

    except Exception as e:
        lock.acquire()
        print('出现错误啦~错误是:', e)
        tmp_ip = json_text['http:'].split('//')[1]
        result.remove(tmp_ip)
        lock.release()
