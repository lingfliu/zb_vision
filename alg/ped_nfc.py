import os
import json
import torch
import argparse
from PIL import Image
from torchvision import transforms as T
from alg.nfc_net import get_model
import numpy as np


######################################################################
# Settings
# ---------
# dataset_dict = {
#     'market'  :  'Market-1501',
#     'duke'  :  'DukeMTMC-reID',
# }
# num_cls_dict = { 'market':30, 'duke':23 }
# num_ids_dict = { 'market':751, 'duke':702 }

transforms = T.Compose([
    T.Resize(size=(288, 144)),
    T.ToTensor(),
    T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

datasets = ['market', 'duke']
dataset = 'market'
backbones = ['resnet50', 'resnet34', 'resnet18', 'densenet121']
backbone = 'resnet50'



class NfcInference(object):
    def __init__(self, dataset):
        cwd = os.path.abspath(__file__)
        cwd = os.path.abspath(os.path.dirname(cwd))

        with open(cwd+'/nfc_doc/label.json', 'r') as f:
            self.label_list = json.load(f)[dataset]
        with open(cwd+'/nfc_doc/attribute.json', 'r') as f:
            self.attribute_dict = json.load(f)[dataset]
        self.dataset = dataset
        self.num_label = len(self.label_list)
        self.model_name = 'resnet50_nfc'
        self.model = get_model(self.model_name, self.num_label, use_id=False, num_id=None)
        self.model.eval()

    def decode(self, pred):
        # 性别
        gender_idx = 12
        if pred[gender_idx] > 0.5:
            gender = 'male'
        else:
            gender = 'female'

        # 1. 上衣颜色
        color_up = ['black', 'white', 'red', 'purple', 'yellow', 'gray', 'blue', 'green']
        up_color_idx = [13, 14, 15, 16, 17, 18, 19, 20]

        slice = [pred[up_color_idx[i]] for i in range(len(up_color_idx))]
        idx = np.where(slice==np.max(slice))
        up_cloth_color = color_up[idx[0][0]]

        # 2. 下衣颜色
        color_down = ['black', 'white', 'pink', 'purple', 'yellow', 'gray', 'blue', 'green', 'brown']
        down_color_idx = [21, 22, 23, 24, 25, 26, 27, 28, 29]

        slice = [pred[down_color_idx[i]] for i in range(len(down_color_idx))]
        idx = np.where(slice==np.max(slice))
        down_cloth_color = color_down[idx[0][0]]

        return (gender, up_cloth_color, down_cloth_color)

        # pred = pred.squeeze(dim=0)
        # for idx in range(self.num_label):
        #     name, chooce = self.attribute_dict[self.label_list[idx]]
        #     if chooce[pred[idx]]:
        #         print('{}: {}'.format(name, chooce[pred[idx]]))

    def inference(self, img):
        src = transforms(img)
        src = src.unsqueeze(dim=0)
        out = self.model.forward(src)
        pred = out.detach().numpy()
        # print('pred length={}'.format(len(pred)))
        # pred = torch.gt(out, torch.ones_like(out)/2 )  # threshold=0.5

        return self.decode(pred[0])

nfc = NfcInference(dataset)

def inference(img):
    return nfc.inference(img)

'''test code'''
# if __name__ == '__main__':
#     nfc = NfcInference(dataset)
#     img = Image.open('../live1.jpg')
#     nfc.inference(img)