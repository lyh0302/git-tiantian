# -- coding: UTF-8
from django.conf.urls import include, url
from user import views

urlpatterns = [

    url(r'^index$', views.index,name="index"),
    url(r'^login$',views.LoginView.as_view(),name="login"),
    url(r'^register$',views.RegisterView.as_view(),name="register"),
    url(r'^active/(?P<token>.*)$',views.ActiveView.as_view(),name='active'),
    url(r'^verificationcode$',views.verificationcode),
    url(r'^set_session$', views.session, name="set_session"),
    # url(r'^checkusername$',views.checkusername),
]