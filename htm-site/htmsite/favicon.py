import os
from pyramid.response import FileResponse
from pyramid.view import view_config


@view_config(route_name="favicon")
def favicon_view(request):
    here = os.path.dirname(__file__)
    icon = os.path.join(here, "assets", "favicon.ico")
    return FileResponse(icon, request=request)
