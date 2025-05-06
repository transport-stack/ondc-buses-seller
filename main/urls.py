import os

from django.urls import path, include
from rest_framework import routers

from main.views import (
    Search,
    Select,
    Init,
    Status,
    Confirm,
    Update,
    ReceiverRecon,
    FetchFare,
)
from main.views.validate_qr import ValidateQRString

app_name = 'main'
IS_STAG = os.getenv("IS_STAG", "False") == "True"

router = routers.DefaultRouter(trailing_slash=False)
search_url = 'search' if IS_STAG else 'subscribe/search'
router.register(search_url, Search, 'ondc_search')  # TODO: For staging build change "subscribe/search" to "search"
router.register(r'select', Select, 'ondc_select')
router.register(r'init', Init, 'ondc_init')
router.register(r'status', Status, 'status')
router.register(r'confirm', Confirm, 'ondc_confirm')
router.register('update', Update, 'ondc_update')
router.register('receiver_recon', ReceiverRecon, 'ondc_receiver_recon')
router.register(r'fetch_fare', FetchFare, 'fetch_fare')
router.register(r'validate_qr', ValidateQRString, 'validate_qr')


urlpatterns = [
    path('', include(router.urls)),
]
