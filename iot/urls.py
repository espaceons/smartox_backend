from django.urls import path
from iot.views import home, api_sync_box

urlpatterns = [
    path('', home, name='home'),
    path('api/iot/sync/', api_sync_box, name='api_sync_box'),
]