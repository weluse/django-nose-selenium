from django.conf.urls.defaults import patterns, url
from . import views


urlpatterns = patterns(
    '',
    url(r'^view1/', views.view1),
    url(r'^view2/', views.view2)
)
