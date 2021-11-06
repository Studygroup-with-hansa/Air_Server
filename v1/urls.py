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
    path('user/data/stats/', views.getStatsOfPeriod.as_view(), name='index'),
    path('user/data/subject/manage/', views.subject.as_view(), name='index'),
    path('user/data/subject/history/', views.getUserSubjectHistory.as_view(), name='index'),
    path('user/data/subject/', views.getUserSubject.as_view(), name='index'),
    path('user/data/subject/targettime/', views.targetTime.as_view(), name='index'),
    path('user/data/subject/checklist/', views.todoList_API.as_view(), name='index'),
    path('user/data/subject/checklist/status/', views.todoListState.as_view(), name='index'),
    path('user/timer/start/', views.startTimer.as_view(), name='index'),
    path('user/timer/stop/', views.stopTimer.as_view(), name='index'),
    path('user/data/group/', views.groupAPI.as_view(), name='index'),
    path('user/data/group/detail/', views.groupDetailAPI.as_view(), name='index'),
    path('user/data/group/detail/user/', views.groupUserAPI.as_view(), name='index'),
    # path('user/data/group/detail/user/manage/', views.groupUserManageAPI.as_view(), name='index'),
]
