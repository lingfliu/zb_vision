import requests
import os
import cv2
from PIL import Image
import time

loadimg_url = 'http://139.9.127.219:8090/media/itemcheckpic'
img_url = "http://139.9.127.219:8090/ismsapi/create_prjcheck_pic/";



for _ in range(5):
    video = cv2.VideoCapture(0)
    return_val, frame = video.read()
    while not return_val:
        time.sleep(0.1)
        return_val, frame = video.read()

    img = Image.fromarray(frame)

    img_path ='/tmp/test_{}.jpg'.format(int(time.time()*1000))
    filename = os.path.basename(img_path)
    img_file = img.save(img_path)

    file = {
        'picfile':open(img_path, 'rb')
    }
    params = {
        'fid': '8b957f12a0b611ea8e33fa163e13886f',
    }

    print('sending img', img_path)
    try:
        response = requests.post(img_url, params=params, files=file, timeout=2)
    except:
        print('uploading timeout')
        continue
    print(response)
    time.sleep(0.1)




