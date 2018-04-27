from bson import json_util
import json


class BaseRenderer:
    content_type = 'text/html'

    def _set_ct(self, system):
        request = system.get('request')
        if request is not None:
            response = request.response
            ct = response.content_type
            if ct == response.default_content_type:
                response.content_type = self.content_type


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
        return json_util.dumps(value, separators=(',', ':'))
        # return '['+(','.join([json.dumps(i,default=json_util.default) for i in value]))+']'


class ZipRenderer:
    content_type = 'application/zip'

    def __init__(self, info):
        pass

    def __call__(self, data, system):
        request = system.get('request')
        if request is not None:
            response = request.response
            ct = response.content_type
            if ct == response.default_content_type:
                response.content_type = self.content_type

        return data.getvalue()
