from django.conf.urls.defaults import patterns, url
from django.views.generic import TemplateView
from . import views


urlpatterns = patterns(
    '',
    url(r'^$', TemplateView.as_view(template_name="myapp/index.html")),
    url(r'^view1/', views.view1),
    url(r'^view2/', views.view2)
)
