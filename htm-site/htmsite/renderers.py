from bson import json_util
import json


class BSONRenderer:
    def __init__(self, info):
        """ Constructor: info will be an object having the
        following attributes: name (the renderer name), package
        (the package that was 'current' at the time the
        renderer was registered), type (the renderer type
        name), registry (the current application registry) and
        settings (the deployment settings dictionary). """
        pass

    def __call__(self, value, system):
        return json.dumps(value, default=json_util.default)


class PymongoCursorRenderer:
    def __init__(self, info):
        pass

    def __call__(self, value, system):
        return '['+(','.join([json.dumps(i,default=json_util.default) for i in value]))+']'
