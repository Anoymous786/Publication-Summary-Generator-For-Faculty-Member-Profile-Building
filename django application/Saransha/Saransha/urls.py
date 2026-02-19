from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_page, name='upload'),
    path('generate-summary/', views.generatesummary, name='generatesummary'),
    path('settings/', views.settings, name='settings'),
    path('login/', views.login, name='login'),
    path('help/', views.help, name='help'),
    path('admin/', admin.site.urls),
    path('graph/', include('graph_app.urls')),
    path('signup/', views.signup, name="signup"),
    path('logo/', views.logo_view, name='logout'),
    path('cust/', views.cust_view, name='cust'),
    path('missVal/', views.missVal_view, name='missVal'),
    path('upload-redirect/', views.upload_redirect, name='upload_redirect'),
    path('payment/', views.payment, name='payment'),
]