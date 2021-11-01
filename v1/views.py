import json

from rest_framework.views import APIView
from .services.returnStatusForm import *
from .services.randomCharCreator import createRandomChar as randCode
from .services.sendSMTP import send
from datetime import datetime, timedelta, date

from django.db.models import Q
from django.http import QueryDict
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.authtoken.models import Token
from .models import *

@method_decorator(csrf_exempt, name='dispatch')
class requestEmailAuth(APIView):
    def post(self, request):
        try:
            email = request.data['email']
        except (KeyError, ValueError):
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        try:
            User.objects.get(email=email)
        except ObjectDoesNotExist:
            code = randCode(8).upper()
            authModel = emailAuth(
                mail=email,
                authCode=code
            )
            send(code, email)
            authModel.save()
            return JsonResponse(OK_200(data={"isEmailExist": False, "emailSent": True}), status=200)
        except (KeyError, ValueError):
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)

        code = randCode(8).upper()
        send(code, email)
        authModel = emailAuth(
            mail=email,
            authCode=code
        )
        authModel.save()
        return JsonResponse(OK_200(data={"isEmailExist": True, "emailSent": True}), status=200)

    def put(self, request):
        try:
            authCode_req = request.data['auth'].upper()
            email = request.data['email']
        except (KeyError, ValueError):
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing'), status=400)
        authModel = emailAuth.objects.get(mail=email)
        authCode = authModel.authCode
        authTime = authModel.reqeustTime
        if authCode == authCode_req:
            pass
        else:
            return JsonResponse(CUSTOM_CODE(status=401, message='invalid auth code', data={"token": ""}), status=401)
        validTimeChecker = timezone.now() - timedelta(minutes=5)
        if authTime < validTimeChecker:
            return JsonResponse(CUSTOM_CODE(status=410, message='time limit exceeded (5min)', data={"token": ""}), status=410)

        userPasswd = randCode(60)
        userModel = User.objects.create_user(
            passwd=userPasswd,
            email=email,
            password=userPasswd,
            username='익명'
        )
        userModel.save()
        try:
            token = Token.objects.create(user=userModel)
        except IntegrityError:
            token = Token.objects.get(user=userModel)
        return JsonResponse(OK_200(data={"token": token.key}), status=200)


@method_decorator(csrf_exempt, name='dispatch')
class modifyUserEmail(APIView):
    def post(self, request):
        try:
            email = request.data['email']
        except (KeyError, ValueError):
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        try:
            User.objects.get(email=email)
        except ObjectDoesNotExist:
            try:
                userModel = request.user
                authCode = randCode(8).upper()
                userModel.newMail = email
                userModel.authCode = authCode
                userModel.requestTime = timezone.now()
                userModel.save()
                send(authCode, email)
                return JsonResponse(OK_200(data={"isEmailExist": False, "emailSent": True}), status=200)
            except (KeyError, ValueError):
                return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        return JsonResponse(BAD_REQUEST_400(message='Given email already Exists', data={"isEmailExist": True, "emailSent": False}), status=400)

    def put(self, request):
        try:
            authCode = request.data['auth'].upper()
        except (KeyError, ValueError):
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing'), status=400)
        userModel = request.user
        if userModel.authCode == authCode:
            pass
        else:
            return JsonResponse(CUSTOM_CODE(status=401, message='invalid auth code', data={}), status=401)
        validTimeChecker = timezone.now() - timedelta(minutes=5)
        if userModel.requestTime < validTimeChecker:
            return JsonResponse(CUSTOM_CODE(status=410, message='time limit exceeded (5min)', data={}), status=410)
        userModel.delete()
        userModel.email = userModel.newMail
        userModel.save()
        try:
            token = Token.objects.create(user=userModel)
        except IntegrityError:
            token = Token.objects.get(user=userModel)
        return JsonResponse(OK_200(data={"token": token.key}), status=200)


@method_decorator(csrf_exempt, name='dispatch')
class modifyUserName(APIView):
    def put(self, request):
        try:
            newName = request.data['name']
        except (KeyError, ValueError):
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing'), status=400)
        try:
            userModel = request.user
            userModel.username = newName
            userModel.save()
            return JsonResponse(OK_200(), status=200)
        except (KeyError, ValueError):
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing'), status=400)
        except Exception as E:
            print(E)
            return JsonResponse(CUSTOM_CODE(status=500, message='Unknown Server Error Accorded'), status=500)


@method_decorator(csrf_exempt, name='dispatch')
class getUserBasicInfo(APIView):
    def get(self, request):
        try:
            userModel = request.user
            email = userModel.email
            name = userModel.username
            return JsonResponse(OK_200(data={"email": email, "name": name}))
        except Exception as E:
            print(E)
            return JsonResponse(CUSTOM_CODE(status=500, message='Unknown Server Error Accorded'), status=500)


@method_decorator(csrf_exempt, name='dispatch')
class checkTokenValidation(APIView):
    def get(self, request):
        userModel = request.user
        return JsonResponse(CUSTOM_CODE(status=200, data={}, message='Valid Token'), status=200)


@method_decorator(csrf_exempt, name='dispatch')
class alterUser(APIView):
    def delete(self, request):
        userModel = request.user
        userModel.delete()
        return JsonResponse(OK_200(data={}), status=200)


@method_decorator(csrf_exempt, name='dispatch')
class subject(APIView):
    def post(self, request):
        try:
            subjTitle = request.data['title']
            subjColor = request.data['color']
        except (KeyError, ValueError):
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        try:
            userSubject.objects.get(user=request.user, title=subjTitle)
            return JsonResponse(BAD_REQUEST_400(message="Same subject is already exists", data={}), status=400)
        except ObjectDoesNotExist:
            subjectModel = userSubject(
                user=request.user,
                title=subjTitle,
                color=subjColor
            )
            subjectModel.save()
            return JsonResponse(OK_200(data={}), status=200)


    def delete(self, request):
        try:
            subjTitle = request.query_params['title']
        except (KeyError, ValueError):
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        try:
            subjectDB = userSubject.objects.get(user=request.user, title=subjTitle)
            subjectDB.delete()
            return JsonResponse(OK_200(data={}), status=200)
        except ObjectDoesNotExist:
            return JsonResponse(BAD_REQUEST_400(message="Subject "+subjTitle+" is not exists", data={}), status=400)
        except Exception as E:
            print(E)
            return JsonResponse(CUSTOM_CODE(status=500, message='Unknown Server Error Accorded', data={}), status=500)


    def put(self, request):
        try:
            subjectTitle = request.query_params['title']
        except (KeyError, ValueError):
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        try:
            subjectDB = userSubject.objects.get(user=request.user, title=subjectTitle)
        except ObjectDoesNotExist:
            return JsonResponse(BAD_REQUEST_400(message="Subject " + subjectTitle + " is not exists", data={}), status=400)
        try:
            title_new = request.query_params['title_new']
            subjectDB.title = title_new
        except (KeyError, ValueError):
            pass
        try:
            color_new = request.query_params['color']
            subjectDB.color = color_new
        except (KeyError, ValueError):
            pass
        subjectDB.save()
        return JsonResponse(OK_200(data={}))


@method_decorator(csrf_exempt, name='dispatch')
class getUserSubjectHistory(APIView):
    def post(self, request):
        if not request.user.is_authenticated or request.user.is_anonymous:
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        try:
            _date = request.data['date']
            _date = _date.split('-')
            try:
                year = int(_date[0])
                month = int(_date[1])
                day = int(_date[2])
                _date = date(year, month, day)
            except (IndexError, TypeError):
                return JsonResponse(BAD_REQUEST_400(message='invalid date given', data={}), status=400)
        except (KeyError, ValueError):
            _date = datetime.now()
        daily = Daily.objects.get(userInfo=request.user, date=_date)
        subjectHistory = dailySubject.objects.filter(dateAndUser=daily)
        subjectHistory = list(subjectHistory)
        returnValue = {"totalTime": 0, "subject": [], "goal": daily.goal}
        for _subjectHistory in subjectHistory:
            if _subjectHistory.time:
                returnValue["totalTime"] = returnValue["totalTime"] + _subjectHistory.time
                subjectDict = {
                    "title": _subjectHistory.title,
                    "time": _subjectHistory.time,
                    "color": _subjectHistory.color
                }
                returnValue["subject"].append(subjectDict)
        return JsonResponse(OK_200(data=returnValue), status=200)


@method_decorator(csrf_exempt, name='dispatch')
class getUserSubject(APIView):
    def get(self, request):
        if not request.user.is_authenticated or request.user.is_anonymous:
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing'), status=400)
        userSubjects = userSubject.objects.filter(user=request.user)
        userSubjects = list(userSubjects)
        returnValueData = {"subject": [], "goal": 0}
        returnValueData["goal"] = request.user.targetTime
        for _userSubject in userSubjects:
            data = {
                "title": str(_userSubject.title),
                "color": str(_userSubject.color)
            }
            returnValueData["subject"].append(data)
        return JsonResponse(OK_200(data=returnValueData), status=200)


@method_decorator(csrf_exempt, name='dispatch')
class targetTime(APIView):
    def post(self, request):
        if not request.user.is_authenticated or request.user.is_anonymous:
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing'), status=400)
        try:
            time = request.data['targetTime']
        except (KeyError, ValueError):
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing'), status=400)
        request.user.targetTime = int(time)
        request.user.save()
        return JsonResponse(OK_200(data={}), status=200)

    def get(self, request):
        if not request.user.is_authenticated or request.user.is_anonymous:
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing'), status=400)
        return JsonResponse(CUSTOM_CODE(status=200, message="OK", data={"targetTime": int(request.user.targetTime)}), status=200)


@method_decorator(csrf_exempt, name='dispatch')
class todoList_API(APIView):
    def post(self, request):
        if not request.user.is_authenticated or request.user.is_anonymous:
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing'), status=400)
        try:
            subjectTitle = request.data['subject']
            todo = request.data['todo']
        except (KeyError, ValueError):
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing'), status=400)
        try:
            _date = request.data['date']
            _date = _date.split('-')
            try:
                year = int(_date[0])
                month = int(_date[1])
                day = int(_date[2])
                _date = date(year, month, day)
            except (IndexError, TypeError):
                return JsonResponse(BAD_REQUEST_400(message='invalid date given', data={}), status=400)
            today = datetime.now()
            if _date.year == today.year and _date.day == today.day:
                isToday = True
            else:
                isToday = False
        except (KeyError, ValueError):
            _date = datetime.now()
            isToday = True
        if isToday:
            try:
                todoSubject = userSubject.objects.get(user=request.user, title=subjectTitle)
            except ObjectDoesNotExist:
                return JsonResponse(BAD_REQUEST_400(message="Subject " + subjectTitle + " is not exists", data={}), status=400)
            try:
                todoDate = Daily.objects.get(userInfo=request.user, date=datetime.now())
                todoSubject = dailySubject.objects.get(dateAndUser=todoDate, title=subjectTitle)
            except ObjectDoesNotExist:
                todoDate = Daily(
                    userInfo=request.user,
                    date=datetime.today(),
                    goal=request.user.targetTime
                )
                todoDate.save()
                todoSubject = dailySubject(
                    dateAndUser=todoDate,
                    title=todoSubject.title,
                    color=todoSubject.color,
                    time=0
                )
                todoSubject.save()
        else:
            try:
                todoDate = Daily.objects.get(userInfo=request.user, date=_date)
                todoSubject = dailySubject.objects.get(dateAndUser=todoDate, title=subjectTitle)
            except ObjectDoesNotExist:
                return JsonResponse(BAD_REQUEST_400(message="Subject " + subjectTitle + " is not exists", data={}), status=400)
        try:
            _todoList = todoList.objects.get(subject=todoSubject)
            _todoList.todo = str(todo)
            _todoList.save()
            pk = _todoList.primaryKey
            return JsonResponse(OK_200(data={"pk": pk}), status=200)
        except ObjectDoesNotExist:
            _todoList = todoList(
                subject=todoSubject,
                isItDone=False,
                todo=str(todo)
            )
            _todoList.save()
            pk = _todoList.primaryKey
            return JsonResponse(OK_200(data={"pk": pk}), status=200)

    def put(self, request):
        try:
            pk = request.query_params['pk']
        except (KeyError, ValueError):
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        try:
            bodyParam = json.loads(request.body)
            todo = bodyParam["todo"]
        except (KeyError, ValueError, json.JSONDecodeError, TypeError):
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        try:
            todoObj = todoList.objects.get(primaryKey=pk)
        except ObjectDoesNotExist:
            return JsonResponse(BAD_REQUEST_400(message="There's no checklist", data={}), status=400)
        if not todoObj.subject.dateAndUser.userInfo == request.user:
            return JsonResponse(BAD_REQUEST_400(message="There's no checklist", data={}), status=400)
        todoObj.todo = str(todo)
        todoObj.save()
        return JsonResponse(OK_200(data={}), status=200)


@method_decorator(csrf_exempt, name='dispatch')
class startTimer(APIView):
    def post(self, request):
        try:
            subjectTitle = request.data['title']
        except (KeyError, ValueError):
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        userDB = request.user
        if not userDB.is_authenticated or userDB.is_anonymous:
            return JsonResponse(INVALID_TOKEN(), 401)
        if userDB.isTimerRunning:
            return JsonResponse(CUSTOM_CODE(message="Timer is already running", status=409, data={}), status=409)
        try:
            runningSubject = userSubject.objects.get(user=userDB, title=subjectTitle)
        except ObjectDoesNotExist:
            return JsonResponse(BAD_REQUEST_400(message="Subject " + subjectTitle + " is not exists", data={}), status=400)
        try:
            daily = Daily.objects.get(userInfo=userDB, date=timezone.now())
        except ObjectDoesNotExist:
            daily = Daily(
                userInfo=userDB,
                date=timezone.now(),
                goal=userDB.targetTime
            )
            daily.save()
            todaySubject = dailySubject(
                dateAndUser=daily,
                title=runningSubject.title,
                color=runningSubject.color,
                time=0
            )
            todaySubject.save()
        try:
            todaySubject = todaySubject
            pass
        except NameError:
            try:
                todaySubject = dailySubject.objects.get(dateAndUser=daily, date=timezone.now())
            except ObjectDoesNotExist:
                todaySubject = dailySubject(
                    dateAndUser=daily,
                    title=runningSubject.title,
                    color=runningSubject.color,
                    time=0
                )
                todaySubject.save()
            userDB.timerRunningSubject = todaySubject
            userDB.save()
        userDB.isTimerRunning = True
        userDB.timerRunningSubject = runningSubject
        userDB.timerStartTime = timezone.now()
        userDB.save()
        return JsonResponse(OK_200(data={}), status=200)


@method_decorator(csrf_exempt, name='dispatch')
class stopTimer(APIView):
    def post(self, request):
        try:
            userDB = request.user
            timeProgress = timezone.now() - request.user.timerStartTime
            daily = Daily.objects.get(userInfo=userDB, date=timezone.now())
            _runningSubject = userSubject.objects.get(primaryKey=userDB.timerRunningSubject_id)
            runningSubject = dailySubject.objects.get(dateAndUser=daily, title=_runningSubject.title)
            runningSubject.time = int(timeProgress.total_seconds())
            runningSubject.save()
            userDB.isTimerRunning = False
            userDB.timerRunningSubject = None
            userDB.timerStartTime = None
            userDB.save()
            return JsonResponse(OK_200(data={}), status=200)
        except (ObjectDoesNotExist, TypeError):
            return JsonResponse(CUSTOM_CODE(message="Timer is already stopped", data={}, status=409), status=409)
