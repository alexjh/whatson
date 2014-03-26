# Create your views here.
"""Views for the whatson app"""

from django.http import HttpResponse
from django.template import RequestContext, loader

def index(request):
    """Main page of the whatson app"""
    template = loader.get_template('whatson/index.html')
    context = RequestContext(request, {
                    })
    return HttpResponse(template.render(context))

