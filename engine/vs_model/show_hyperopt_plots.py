import yaml

with open("../../connection.yaml") as infile:
    conf = yaml.load(infile)
mongo_uri = conf['mongo_uri']
from PIL import Image
from pymongo import MongoClient
from base64 import b64decode
from io import BytesIO

client = MongoClient(mongo_uri)
res = list(client['jobs']['jobs'].find({
    'exp_key': 'lstm_115_2_redo',
    'result.loss': {'$ne': float('nan')},
    'result.status': 'ok',
}).sort([('result.metrics.rmse', 1)]))
for i in range(3):
    # print(res[i]['result']['params'])
    if type(res[i]['result']['figure']) is bytes:
        im = Image.open(BytesIO(res[i]['result']['figure']))
    else:
        im = Image.open(BytesIO(b64decode(res[i]['result']['figure'])))
    im.show()

from theano import tensor
a = tensor.log(5)
a.eval
