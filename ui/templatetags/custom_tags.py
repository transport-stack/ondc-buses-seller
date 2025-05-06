from django import template
from requests.models import PreparedRequest

register = template.Library()


@register.simple_tag
def url_replace(request, field, value):
    dict_ = request.GET.copy()
    dict_[field] = value
    return dict_.urlencode()


@register.simple_tag
def get_data_export_url(request):
    params = {"export": "true", "page_length": "MAX"}
    req = PreparedRequest()
    req.prepare_url(request.build_absolute_uri(), params)
    return req.url
