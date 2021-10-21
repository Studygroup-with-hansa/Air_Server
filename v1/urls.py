from django.urls import path, include
from . import views

app_name = 'v1'
urlpatterns = [
    path('user/manage/signin/', views.requestEmailAuth.as_view(), name='index'),
    path('user/info/manage/basic/email/', views.modifyUserEmail.as_view(), name='index'),
    path('user/info/manage/basic/name/', views.modifyUserName.as_view(), name='index'),
    path('user/info/manage/basic/', views.getUserBasicInfo.as_view(), name='index'),
    path('user/info/manage/basic/checktoken/', views.checkTokenValidation.as_view(), name='index'),
    path('user/info/manage/', views.alterUser.as_view(), name='index'),
    path('user/data/subject/manage/', views.subject.as_view(), name='index'),
    path('user/timer/start/', views.startTimer.as_view(), name='index'),
    path('user/timer/stop/', views.stopTimer.as_view(), name='index'),
]
