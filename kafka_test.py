import pickle
import json
from utils import *
from kafka import KafkaProducer


servers = ['10.89.8.166:9092', '10.89.8.225:9092','10.89.8.71:9092']
k_producer = KafkaProducer(bootstrap_servers=servers)
k_topic = 'iot_video_monitor'
k_key = ''


data = {
    'macAdder':"00-00-00-00-00-00",
    'timeStamp':str(current_time_ms()),
    'messageType':3,
    'deriverId':1,
    'count':1,
    'clothing':'255,255,0:128,128,128',
    'ipcId':'X86_SOT_ModelA_00000',
    'pic':'http://139.9.127.219:8090/media/itemcheckpic/00000000.jpg'
}


tic = current_time_ms()
for _ in range(100):
    future = k_producer.send(k_topic, value=bytes(json.dumps(data), 'utf-8'))
    result = future.get(60)
    toc = current_time_ms()
    print('msg sent', result)
    print('sending cost {} ms'.format(toc-tic))
    tic = toc
# k_producer.send(k_topic, value=b'test from python')
