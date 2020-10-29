ZB Vision 正邦视觉分析算法引擎

Developped by Lingfeng Liu 

email:lingfeng.liu@163.com

All rights reserved

禁止用于商业用途

Ver. 1.0

###功能
1. 基于Restful的服务配置与状态查询
2. 面向多摄像头接入的视频抽帧的图像截取
3. 深度神经网络的人员检测与工服颜色分析

###部署环境
    - Python 3.7
    - Tensorflow 1.14.0
    - Keras 2.2.5
    - Opencv-python 4.4.0
    - PyTorch ~
    - PIL ~
    - Flask ~
    - gevent ~
    - Django 2.1.4
    - Rx ~

###模型文件存放位置
  alg/nfc_checkpoints
  	duke/resnet50_nfc/net_last.pth
  	market/densenet121_nfc/net_last.pth
  	resnet50_nfc/net_last.pth
  	
  alg/yolo3_model_data/
  	zb.h5
  	zb_anchors.txt
  	zb_classes.txt
    

### 运行方式 

`python server.py`

