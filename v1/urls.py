from django.urls import path, include
from . import views

app_name = 'v1'
urlpatterns = [
    path('user/manage/signin/', views.requestEmailAuth.as_view(), name='index'),
]
