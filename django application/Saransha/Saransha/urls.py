"""
URL configuration for Saransha project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [

    path('',views.home,name='home'),
    path('upload/', views.upload_page, name='upload'),
    path('generate-summary/', views.generatesummary, name='generatesummary'),
    path('settings/', views.settings, name='settings'),
    path('login/', views.login, name='login'),
    path('help/', views.help, name='help'),
    path('payment/', views.payment, name='payment'),
    path('admin/', admin.site.urls),
    path('graph/', include('graph_app.urls')),
    path('signup/',views.signup,name="signup"),
    path('logo/', views.logo_view, name='logout'),
    path('cust/', views.cust_view, name='cust'),
    path('missVal/', views.missVal_view, name='missVal'),
    path('upload-redirect/', views.upload_redirect, name='upload_redirect'),
    path('api/chat-with-researcher/', views.chat_with_researcher, name='chat_with_researcher'),


]