from django.urls import path, include
from . import views

app_name = 'v1'
urlpatterns = [
    path('user/manage/signin/', views.requestEmailAuth.as_view(), name='index'),
    path('user/info/manage/basic/email/', views.modifyUserEmail.as_view(), name='index'),
    path('user/info/manage/basic/name/', views.modifyUserName.as_view(), name='index'),
]
