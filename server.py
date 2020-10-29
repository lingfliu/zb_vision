# -*- coding: UTF-8 -*-

from flask import Flask, request, make_response
import json
import queue
import pickle
import os
from kafka import KafkaProducer
from utils import *

from cv_ped import PedDetector
from concurr_tool import CyclicTask

from PIL import Image
import requests

import gevent



'''=====================
基于Flask的行人检测算法服务
采用pickle文件作为简易配置
运行方式：直接运行
版本依赖：
    1. Tensorflow 1.14
    2. Keras 2.2.5
    3. PyTorch ~ 
    4. Numpy ~
    5. Flask  ~
    6. Kafka ~
    7. Pillow ~
    8. Opencv-python 4.4
========================'''

system_storepath = os.path.expanduser('~')+'/zb_vision.cfg'

'''======================='''
'''system config'''
'''======================='''
def load_system():
    if not os.path.exists(system_storepath):
        system = {
            'rtsp_addr': {},  # rtsp端列表 [id:(addr)]
            'rtsp_stat': {},  # rtsp端列表 [id:(enabled, conn, fps)]
            'rtsp_ipc_chan': {}, # rtsp 工控机通道列表
            'rtsp_ipc_id': {}, # rtsp 工控机id
            'rtsp_ipc_mac': {},  # rtsp 工控机 mac

            'max_rtsp_conn': 2,
            'enabled': True  #是否全局打开
        }
        with open(system_storepath, 'wb+') as f:
            pickle.dump(system, f)
    else:
        with open(system_storepath, 'rb') as f:
            system = pickle.load(f)

    return system

def save_system():
    with open(system_storepath, 'wb+') as f:
        pickle.dump(system, f)

system = load_system()

'''======================='''
'''pedestrian detector    '''
'''======================='''
ped_detector = PedDetector()
def _init_ped_detect():
    for id in system['rtsp_addr']:
        addr = system['rtsp_addr'][id]
        ped_detector.add_rtsp_client(id, addr)
        enabled = system['rtsp_stat']
        if not enabled:
            ped_detector.disable_detect(id)
    if not system['enabled']:
        ped_detector.stop()
    else:
        ped_detector.start()

'''========================'''
'''flask http server config'''
'''========================'''
app = Flask(__name__)

def create_response_ok():
    return make_response(json.dumps({'result':'ok'}), 200)

def create_response_fail(err):
    return make_response(json.dumps({'result':'fail', 'err':err}), 200)

'''获取全局配置信息'''
@app.route('/api/cfg/global', methods=['GET'])
def get_global_cfg():
    cfg = {
        'rtsp_max_num':system['max_rtsp_conn'], # 最大rtsp接入数量
        'enabled': system['enabled'] # 是否开启算法
    }
    return json.dumps(cfg)

@app.route('/api/cfg/global/rtsp_num', methods=['POST'])
def set_max_rtsp():
    system['max_rtsp_conn'] = request.args.get('num')

    save_system()
    return create_response_ok()

@app.route('/api/cfg/rtsp', methods=['GET'])
def get_rtsp_list():
    rtsp_info =  {}
    for id in system['rtsp_addr']:
        rtsp_info[id] = {
            'addr':system['rtsp_addr'][id],
            'ipc_chan':system['rtsp_ipc_chan'][id],
            'ipc_mac':system['rtsp_ipc_mac'][id],
            'ipc_id':system['rtsp_ipc_id'],
            'conn':ped_detector.conn_map[id],
            'fps':ped_detector.fps_map[id],
            'enabled':system['rtsp_stat'][id][0]}
    return json.dumps(rtsp_info)

@app.route('/api/test/rtsp', methods=['POST'])
def add_rtsp_test():
    id = '_test'
    system['rtsp_addr'][id] = 0
    system['rtsp_stat'][id] = (True, 100, 0)
    system['rtsp_ipc_chan'][id] = '0'
    system['rtsp_ipc_mac'][id] = '00-00-00-00-00-00'
    system['rtsp_ipc_id'][id] = 'amd64_test'

    save_system()

    ped_detector.add_rtsp_client(id, 0)
    ped_detector.enable_detect(id)

    return create_response_ok()
@app.route('/api/test/rtsp', methods=['DELETE'])
def remove_rtsp_test():
    id = '_test'

    delete_rtsp(id)

    del system['rtsp_addr'][id]
    del system['rtsp_stat'][id]

    del system['rtsp_ipc_chan'][id]
    del system['rtsp_ipc_mac'][id]
    del system['rtsp_ipc_id'][id]
    save_system()

    return create_response_ok()


@app.route('/api/cfg/rtsp', methods=['POST'])
def add_rtsp():
    if len(system['rtsp_addr']) >= system['max_rtsp_conn']:
        return create_response_fail('max rtsp connection reached')

    c = request.get_json()
    content = c
    if not 'addr' in c or\
        not 'id' in c or\
        not 'ipc_chan' in c or\
        not 'ipc_mac' in c or\
        not 'ipc_id' in c:
        return create_response_fail('missing address')


    addr = content['addr']
    id = content['id']
    ipc_chan = content['ipc_chan']
    ipc_mac = content['ipc_mac']
    ipc_id = content['ipc_id']

    if len(addr) == 0 or\
        len(id) == 0 or\
        len(ipc_chan) == 0 or\
        len(ipc_mac) == 0 or\
        len(ipc_id) == 0:
        return create_response_fail('missing address')

    system['rtsp_addr'][id] = addr
    system['rtsp_stat'][id] = (True, 100, 0)
    system['rtsp_ipc_chan'][id] = ipc_chan
    system['rtsp_ipc_mac'][id] = ipc_mac
    system['rtsp_ipc_id'][id] = ipc_id

    save_system()

    ped_detector.add_rtsp_client(id, addr)
    ped_detector.enable_detect(id)

    return create_response_ok()

@app.route('/api/cfg/rtsp', methods=['DELETE'])
def delete_rtsp():
    id = request.args.get('id')
    if not id in system['rtsp_addr']:
        return create_response_fail('rtsp not found')

    ped_detector.del_rtsp_client(id)

    del system['rtsp_addr'][id]
    del system['rtsp_stat'][id]
    del system['rtsp_ipc_chan'][id]
    del system['rtsp_ipc_mac'][id]
    del system['rtsp_ipc_id'][id]

    save_system()

    return create_response_ok()


@app.route('/api/cfg/rtsp/enable', methods=['POST'])
def enable_rtsp():
    id = request.args.get('id')
    if not id in system['rtsp_addr']:
        return create_response_fail('rtsp not found')

    enabled = request.args.get('enabled')
    if enabled:
        ped_detector.enable_detect(id)
    else:
        ped_detector.disable_detect(id)

    save_system()

    create_response_ok()

'''======================='''
'''kafka message queue'''
'''======================='''
# kmsg_queue = queue.Queue(maxsize=1000)
k_servers = ['10.89.8.166:9092', '10.89.8.225:9092','10.89.8.71:9092']
k_topic = 'iot_video_monitor'

'''将检测结果转换为kafka消息'''
def res2kmsg(res, load_img_url):
    data = {
        'macAdder':"00-00-00-00-00-00",
        'timeStamp':0,
        'messageType':3,
        'deriverId':1,
        'count':1,
        'clothing':'255,255,0:128,128,128',
        'ipcId':'X86_SOT_ModelA_00000',
        'pic':'http://139.9.127.219:8090/media/itemcheckpic/00000000.jpg'
    }

    # res = (id, img, [(img_crop, bounding_box, result)], t_submit, fps)
    data['timeStamp'] = res[3]
    data['count'] = len(res[2]) # 数量
    data['deriverId'] = int(system['ipc_chan'][res[0]]) # 通道
    data['macAdder'] = system['ipc_mac'][res[0]]
    data['ipcId'] = system['ipc_id'][res[0]]
    up_rgb = color2rgb(res[2][0][2][1])
    down_rgb = color2rgb(res[2][0][2][2])
    data['clothing'] = up_rgb + down_rgb # 第一个人的服装颜色，TODO: 这里需要修改协议
    data['pic'] = load_img_url

    msg = json.dumps(data)
    return msg

def _img_upload(img_path):
    img_url = "http://139.9.127.219:8090/ismsapi/create_prjcheck_pic/";
    file = {
        'picfile': open(img_path, 'rb')
    }
    params = {
        'fid': '8b957f12a0b611ea8e33fa163e13886f',
    }

    try:
        response = requests.post(img_url, params=params, files=file, timeout=4)
        return response.ok
    except:
        print('uploading timeout')
        return False

from concurr_tool import ThreadPool
upload_task_pool = ThreadPool(10, interval=0.05, queueMax=500)
upload_task_pool.start()

def _upload_task(res):
    img_name = 'test_{}.jpg'.format(res[3]) # images named by 'test' + time of submit
    img_path = '/tmp/'+img_name #store the temp snapshots in /tmp
    print('saving', img_path)
    res[1].save(img_path)

    if _img_upload(img_path):
        load_img_url = 'http://139.9.127.219:8090/media/itemcheckpic'+img_name
    else:
        # if failed to upload img, send false img url
        load_img_url = 'http://139.9.127.219:8090/media/itemcheckpic/failed.png'
    try:
        msg = res2kmsg(res, load_img_url)
        k_producer = KafkaProducer(bootstrap_servers=k_servers)
        future = k_producer.send(k_topic, value=bytes(msg, 'utf-8'))
        kresult = future.get(4)
        print('result sent to kafka', kresult)
    except:
        print('failed to connect kafka, waiting')

def _k_task():
    try:
        # print('running here')
        res = ped_detector.result_queue.get(block=True, timeout=0.1)
    except:
        # print('no result, quit')
        return

    if not res:
        # print('no result, quit')
        return

    params = {'res': res}
    upload_task_pool.submit(_upload_task, params)


    # TODO: Remove local image buffers
    # os.remove(img_path)

def main():
    # initialize all tasks

    load_system()
    _init_ped_detect()

    # enable kafka pushing
    k_pusher = CyclicTask(_k_task, (), 0.1)
    k_pusher.start()

    app.run(port=8001)

if __name__ == '__main__':
    main()
