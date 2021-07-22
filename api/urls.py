"""api URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
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
from django.urls import path
from django.views.generic import TemplateView

from system import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', views.login),
    path('api/task/add', views.token_add),
    path('api/task/edit', views.token_edit),
    path('api/task/scan_status', views.scan_status),
    path('api/task/search', views.search),
    path('api/liststatus/',views.liststatus),
    path('api/liststatus/xq',views.listxq),
    path('api/task/del',views.task_del),
    path('api/report/list',views.report_list),
    path('api/liststatus/edit', views.status_edit),
    path('api/del', views.data_del),
    path('api/task/time', views.sj_time),
    path('api/task/time/update/jc', views.time_update_jc),
    path('api/task/time/update/wz', views.time_update_wz),
    path('api/mail/', views.gjmail),
    path('api/liststatus/search/', views.status_search),
    path('api/report/search/', views.report_search),
    path('api/user/list/', views.user_list),
    path('api/user/add/', views.user_add),
    path('api/user/del/', views.user_del),
    path('api/user/edit/', views.user_edit),
    path('api/user/search/', views.user_search),
    path('',TemplateView.as_view(template_name='index.html'))

]

