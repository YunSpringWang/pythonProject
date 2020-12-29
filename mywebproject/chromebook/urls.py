from django.conf.urls import url
from . import views
from django.urls import path
app_name="chromebook"
urlpatterns = [
    url(r'^$', views.homepage),
    url(r'^host_list', views.HostListView),
    url(r'^CheckServerDetailsView', views.CheckServerDetailsView),
]