import queue
import threading
import time
from timeit import default_timer as timer

import cv2
from PIL import Image, ImageFont, ImageDraw
from alg.ped_yolo import detect
from alg.ped_nfc import inference

from concurr_tool import CyclicTask


class Rtsp:
    def __init__(self, id, addr, fps, enabled, stat):
        self.id = id
        self.addr = addr
        self.fps = fps
        self.enabled = enabled
        self.stat = stat

'''行人检测器'''
class PedDetector:
    def __init__(self):
        self.rtsp_addr_map = {} # [id:addr]
        self.video_map = {}
        self.img_cap_map = {}
        self.fps_map = {}
        self.enabled_map = {}
        self.conn_map = {} # [id: (on-/off-line)]

        self.capture_task = {}
        self.detect_task = CyclicTask(_ped_detect_task, (self, ), 0.01)
        self.detect_task.start()

        self.result_queue = queue.Queue(maxsize=1000)

    '''enable detect, connect to rtsp addr, reset stats'''
    def _init_rtsp_client(self, id):
        self.video_map[id] = cv2.VideoCapture(self.rtsp_addr_map[id])
        self.img_cap_map[id] = (None, 0, False)
        self.fps_map[id] = 0
        self.enabled_map[id] = True
        self.conn_map[id] = 100  # 100 for connected 0 for disconnected


    def add_rtsp_client(self, id, addr):
        if id in self.rtsp_addr_map:
            self.update_rtsp_client(id, addr)
            return
        else:
            self.rtsp_addr_map[id] = addr
            self._init_rtsp_client(id)

    def update_rtsp_client(self, id, addr):
        self.rtsp_addr_map[id] = addr
        self._init_rtsp_client(id)
        if self.enabled_map[id]:
            task = CyclicTask(_capture_task, (id, self,), 0.01)
            task.start()
            self.capture_task[id] = task

    def del_rtsp_client(self, id):
        if not id in self.rtsp_addr_map:
            return

        del self.rtsp_addr_map[id]
        del self.video_map[id]
        del self.img_cap_map[id]
        if id in self.capture_task:
            self.capture_task[id].quit()
            del self.capture_task[id]
        del self.fps_map[id]

    def enable_detect(self, id):
        if id in self.capture_task:
            self.capture_task[id].quit()
        task = CyclicTask(_capture_task, (id, self,), 0.01)
        task.start()
        self.capture_task[id] = task

    def disable_detect(self, id):
        if id in self.capture_task:
            self.capture_task[id].quit()

    '''stop capture and detect tasks'''
    def stop(self):
        for id in self.capture_task:
            task = self.capture_task[id]
            task.quit()

        if self.detect_task:
            self.detect_task.quit()

    '''start capture and detect tasks'''
    def start(self):
        for id in self.capture_task:
            self.capture_task[id].quit()
        for id in self.rtsp_addr_map:
            if self.enabled_map[id]:
                task = CyclicTask(_capture_task, (id, self,), 0.01)
                self.capture_task[id] = task
                task.start()

        if self.detect_task:
            self.detect_task.quit()
        self.detect_task = CyclicTask(_ped_detect_task, (self,), 0.01)
        self.detect_task.start()

def _ped_detect_task(ped_detect):
    for id in ped_detect.img_cap_map:
        tic = time.time()
        (img, t_submit, inferred) = ped_detect.img_cap_map[id]
        if not img:
            time.sleep(0.01)
            continue
        if not inferred:
            ped_detect.img_cap_map[id] = (img, t_submit, True)
        else:
            time.sleep(0.01)
            continue

        res = []
        detect_result = detect(img)
        for img_crop, bounding_box, score in detect_result:
            result = inference(img_crop)
            print('cam {} image croped'.format(id), (bounding_box), 'inferred', result[0], result[1], result[2])
            res.append((img_crop, bounding_box, result))
        t_observe = time.time()
        fps = 1 / (t_observe - t_submit)

        # do not transmit zero detection
        if len(res) == 0:
            continue

        ped_detect.fps_map[id] = fps
        try:
            ped_detect.result_queue.put((id, img, res, int(t_submit*1000), fps))
            toc = time.time()
            print('detect {} persons in cam {}, took {} s'.format(len(detect_result), id, toc - tic))
        except:
            print('queue jammed, drop result')



def _capture_task(id, ped_detect):
    conn_val = ped_detect.conn_map[id]
    return_val, frame = ped_detect.video_map[id].read()
    if not return_val:
        print('cam {} offline'.format(id))
        conn_val -= 1
        if conn_val < 0:
            conn_val = 0
        ped_detect.conn_map[id] = conn_val

        v = cv2.VideoCapture(ped_detect.rtsp_addr_map[id])
        ped_detect.video_map[id] = v
        # val, f = ped_detect.video_map[id].read()
        time.sleep(0.5)
        return

    conn_val += 1
    if conn_val > 100:
        conn_val = 100
    ped_detect.conn_map[id] = conn_val
    img = Image.fromarray(frame)
    # print('image captured', img.width, img.height)
    # TODO: determine if image changed
    ped_detect.img_cap_map[id] = (img, time.time(), False)
