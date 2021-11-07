import json
from operator import itemgetter

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
            authCode_req = request.query_params['auth'].upper()
            email = request.query_params['email']
        except (KeyError, ValueError):
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing'), status=400)
        authModel = emailAuth.objects.get(mail=email)
        authCode = authModel.authCode
        authTime = authModel.requestTime
        if authCode == authCode_req:
            pass
        else:
            return JsonResponse(CUSTOM_CODE(status=401, message='invalid auth code', data={"token": ""}), status=401)
        validTimeChecker = timezone.now() - timedelta(minutes=5)
        if authTime < validTimeChecker:
            return JsonResponse(CUSTOM_CODE(status=410, message='time limit exceeded (5min)', data={"token": ""}), status=410)
        try:
            userModel = User.objects.get(email=email)
        except ObjectDoesNotExist:
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
        if not request.user.is_authenticated or request.user.is_anonymous:
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
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
        if not request.user.is_authenticated or request.user.is_anonymous:
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        try:
            authCode = request.query_params['auth'].upper()
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
        if not request.user.is_authenticated or request.user.is_anonymous:
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        try:
            newName = request.query_params['name']
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
        if not request.user.is_authenticated or request.user.is_anonymous:
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
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
        if not request.user.is_authenticated or request.user.is_anonymous:
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        return JsonResponse(CUSTOM_CODE(status=200, data={}, message='Valid Token'), status=200)


@method_decorator(csrf_exempt, name='dispatch')
class alterUser(APIView):
    def delete(self, request):
        if not request.user.is_authenticated or request.user.is_anonymous:
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        userModel = request.user
        userModel.delete()
        return JsonResponse(OK_200(data={}), status=200)


@method_decorator(csrf_exempt, name='dispatch')
class getStatsOfPeriod(APIView):
    def post(self, request):
        if not request.user.is_authenticated or request.user.is_anonymous:
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        try:
            _dateStart = request.data['startDate']
            _dateEnd = request.data['endDate']
            _dateStart = _dateStart.split('-')
            _dateEnd = _dateEnd.split('-')
            try:
                year = int(_dateStart[0])
                month = int(_dateStart[1])
                day = int(_dateStart[2])
                _dateStart = date(year, month, day)
                year = int(_dateEnd[0])
                month = int(_dateEnd[1])
                day = int(_dateEnd[2])
                _dateEnd = date(year, month, day)
            except (IndexError, TypeError):
                return JsonResponse(BAD_REQUEST_400(message='invalid date given', data={}), status=400)
        except (KeyError, ValueError):
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        if _dateStart >= _dateEnd or _dateEnd > datetime.now().date():
            return JsonResponse(BAD_REQUEST_400(message='invalid date given', data={}), status=400)
        returnData = {
            "totalTime": 0,
            "goals": 0,
            "achievementRate": 0,
            "stats": []
        }
        stepDate = _dateStart
        while stepDate <= _dateEnd:
            statForm = {
                "date": str(stepDate.strftime("%Y-%m-%d")),
                "totalStudyTime": 0,
                "achievementRate": 0,
                "subject": [],
                "goal": 0
            }
            try:
                dateObject = Daily.objects.get(userInfo=request.user, date=stepDate)
                statForm["goal"] = dateObject.goal
            except ObjectDoesNotExist:
                returnData["stats"].append(statForm)
                stepDate += timedelta(days=1)
                continue
            statForm["goal"] = dateObject.goal
            subjects = dailySubject.objects.filter(dateAndUser=dateObject)
            subjects = list(subjects)
            if not subjects.__len__():
                returnData["stats"].append(statForm)
                stepDate += timedelta(days=1)
                continue
            else:
                for _subject in subjects:
                    statForm["totalStudyTime"] += _subject.time
                    subjectObject = {
                        "title": _subject.title,
                        "time": _subject.time,
                        "color": _subject.color
                    }
                    statForm["subject"].append(subjectObject)
                try:
                    statForm["achievementRate"] = statForm["totalStudyTime"]/statForm["goal"]*100
                except ZeroDivisionError:
                    statForm["achievementRate"] = 0.0
                returnData["stats"].append(statForm)
            stepDate += timedelta(days=1)
        return JsonResponse(OK_200(data=returnData), status=200)


@method_decorator(csrf_exempt, name='dispatch')
class subject(APIView):
    def post(self, request):
        if not request.user.is_authenticated or request.user.is_anonymous:
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
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
        if not request.user.is_authenticated or request.user.is_anonymous:
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
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
        if not request.user.is_authenticated or request.user.is_anonymous:
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
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
            except ObjectDoesNotExist:
                todoDate = Daily(
                    userInfo=request.user,
                    date=datetime.today(),
                    goal=request.user.targetTime
                )
                todoDate.save()
            try:
                todoSubject = dailySubject.objects.get(dateAndUser=todoDate, title=subjectTitle)
            except ObjectDoesNotExist:
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
            _todoList = todoList(subject=todoSubject, todo=str(todo))
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
        if not request.user.is_authenticated or request.user.is_anonymous:
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
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

    def get(self, request):
        if not request.user.is_authenticated or request.user.is_anonymous:
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        try:
            _date = request.query_params['date']
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
        returnValue = {
            "date": str(_date.strftime("%Y-%m-%d")),
            "memo": "",
            "subjects": [],
        }
        try:
            _day = Daily.objects.get(userInfo=request.user, date=_date)
            subjects = dailySubject.objects.filter(dateAndUser=_day)
            subjects = list(subjects)
        except ObjectDoesNotExist:
            return JsonResponse(OK_200(data=returnValue), status=200)
        returnValue["memo"] = _day.memo
        for subj in subjects:
            data = {
                "subject": subj.title,
                "todoList": []
            }
            todo = todoList.objects.filter(subject=subj)
            todo = list(todo)
            for _todo in todo:
                todo_data = {
                    "pk": _todo.pk,
                    "isitDone": _todo.isItDone,
                    "todo": _todo.todo
                }
                data["todoList"].append(todo_data)
            returnValue["subjects"].append(data)
        return JsonResponse(OK_200(data=returnValue), status=200)

    def delete(self, request):
        if not request.user.is_authenticated or request.user.is_anonymous:
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        try:
            pk = request.query_params['pk']
        except (KeyError, ValueError):
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        try:
            todoListObject = todoList.objects.get(primaryKey=pk)
        except ObjectDoesNotExist:
            return JsonResponse(BAD_REQUEST_400(message="There's no checklist", data={}), status=400)
        if todoListObject.subject.dateAndUser.userInfo == request.user:
            todoListObject.delete()
            return JsonResponse(OK_200(data={}), status=200)
        else:
            return JsonResponse(BAD_REQUEST_400(message="There's no checklist", data={}), status=400)


@method_decorator(csrf_exempt, name='dispatch')
class todoListState(APIView):
    def put(self, request):
        if not request.user.is_authenticated or request.user.is_anonymous:
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        try:
            pk = request.query_params['pk']
        except (KeyError, ValueError):
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        try:
            todoObj = todoList.objects.get(primaryKey=pk)
        except ObjectDoesNotExist:
            return JsonResponse(BAD_REQUEST_400(message="There's no checklist", data={}), status=400)
        if not todoObj.subject.dateAndUser.userInfo == request.user:
            return JsonResponse(BAD_REQUEST_400(message="There's no checklist", data={}), status=400)
        if todoObj.isItDone:
            todoObj.isItDone = False
        else:
            todoObj.isItDone = True
        todoObj.save()
        return JsonResponse(OK_200(data={"isitDone": todoObj.isItDone}), status=200)


@method_decorator(csrf_exempt, name='dispatch')
class memo(APIView):
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
            today = datetime.now()
            if _date.year == today.year and _date.day == today.day:
                isToday = True
            else:
                isToday = False
        except (KeyError, ValueError):
            _date = datetime.now()
            isToday = True
        try:
            memoContent = request.data['memo']
        except (KeyError, ValueError):
            return JsonResponse(BAD_REQUEST_400(message="Some Values are missing"), status=400)
        if isToday:
            try:
                memoDate = Daily.objects.get(userInfo=request.user, date=_date)
                memoDate.todo = str(memoContent)
                memoDate.save()
                return JsonResponse(OK_200(), status=200)
            except ObjectDoesNotExist:
                memoDate = Daily(
                    userInfo=request.user,
                    date=_date,
                    goal=request.user.targetTime,
                    todo=str(memoContent)
                )
                memoDate.save()
                return JsonResponse(OK_200(), status=200)
        else:
            try:
                memoDate = Daily.objects.get(userInfo=request.user, date=_date)
                memoDate.todo = str(memoContent)
                memoDate.save()
                return JsonResponse(OK_200(), status=200)
            except ObjectDoesNotExist:
                return JsonResponse(BAD_REQUEST_400(message='invalid date given', data={}), status=400)


@method_decorator(csrf_exempt, name='dispatch')
class startTimer(APIView):
    def post(self, request):
        if not request.user.is_authenticated or request.user.is_anonymous:
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
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
        except (NameError, UnboundLocalError):
            try:
                todaySubject = dailySubject.objects.get(dateAndUser=daily, title=subjectTitle)
            except ObjectDoesNotExist:
                todaySubject = dailySubject(
                    dateAndUser=daily,
                    title=runningSubject.title,
                    color=runningSubject.color,
                    time=0
                )
                todaySubject.save()
            userDB.timerRunningSubject = runningSubject
            userDB.save()
        userDB.isTimerRunning = True
        userDB.timerRunningSubject = runningSubject
        userDB.timerStartTime = timezone.now()
        userDB.save()
        return JsonResponse(OK_200(data={}), status=200)


@method_decorator(csrf_exempt, name='dispatch')
class stopTimer(APIView):
    def post(self, request):
        if not request.user.is_authenticated or request.user.is_anonymous:
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        try:
            userDB = request.user
            timeProgress = timezone.now() - request.user.timerStartTime
            daily = Daily.objects.get(userInfo=userDB, date=timezone.now())
            _runningSubject = userSubject.objects.get(primaryKey=userDB.timerRunningSubject_id)
            runningSubject = dailySubject.objects.get(dateAndUser=daily, title=_runningSubject.title)
            runningSubject.time += int(timeProgress.total_seconds())
            runningSubject.save()
            daily.totalStudyTime += int(timeProgress.total_seconds())
            daily.save()
            userDB.isTimerRunning = False
            userDB.timerRunningSubject = None
            userDB.timerStartTime = None
            userDB.save()
            return JsonResponse(OK_200(data={}), status=200)
        except (ObjectDoesNotExist, TypeError):
            return JsonResponse(CUSTOM_CODE(message="Timer is already stopped", data={}, status=409), status=409)


@method_decorator(csrf_exempt, name='dispatch')
class groupAPI(APIView):
    def post(self, request):
        if not request.user.is_authenticated or request.user.is_anonymous:
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        try:
            Group.objects.get(leaderUser=request.user)
            return JsonResponse(CUSTOM_CODE(status=409, message='Group is already exists', data={}), status=409)
        except ObjectDoesNotExist:
            while True:
                randomCode = randCode(8).upper()
                try:
                    Group.objects.get(groupCode=randomCode)
                except ObjectDoesNotExist:
                    break
            groupObject = Group(
                groupCode=randomCode,
                leaderUser=request.user,
                userCount=1
            )
            groupObject.save()
            groupObject.user.add(request.user)
            return JsonResponse(OK_200(data={"code": groupObject.groupCode}), status=200)

    def get(self, request):
        if not request.user.is_authenticated or request.user.is_anonymous:
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        try:
            groupObjects = Group.objects.filter(user=request.user)
            groupObjects = list(groupObjects)
            returnValue = {
                "groupList": []
            }
            for groupObject in groupObjects:
                groupValue = {
                    "code": groupObject.groupCode,
                    "userCount": groupObject.userCount,
                    "leader": groupObject.leaderUser.username,
                    "leaderEmail": groupObject.leaderUser.email,
                    "firstPlace": "",
                    "firstPlaceStudyTime": 0
                }
                userObjects = groupObject.user.all()
                userList = list()
                for userObject in userObjects:
                    try:
                        userStudyTimeInfo = {"user": userObject,
                                             "time": Daily.objects.get(userInfo=userObject, date=datetime.now().date())}
                    except ObjectDoesNotExist:
                        userStudyTimeInfo = {"user": userObject, "time": 0}
                    userList.append(userStudyTimeInfo)
                userList = sorted(userList, key=itemgetter('time'))
                groupValue["firstPlace"] = userList[-1]["user"].username
                groupValue["firstPlaceStudyTime"] = userList[-1]["time"]
                returnValue["groupList"].append(groupValue)
            return JsonResponse(OK_200(data=returnValue), status=200)
        except ObjectDoesNotExist:
            return JsonResponse(OK_200(data={"groupList": []}), status=200)

    def delete(self, request):
        if not request.user.is_authenticated or request.user.is_anonymous:
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        try:
            groupObject = Group.objects.get(leaderUser=request.user)
        except ObjectDoesNotExist:
            return JsonResponse(CUSTOM_CODE(status=409, message='There is no Group', data={}), status=409)
        groupObject.delete()
        return JsonResponse(OK_200(data={}), status=200)


@method_decorator(csrf_exempt, name='dispatch')
class groupDetailAPI(APIView):
    def post(self, request):
        try:
            groupCode = request.data['groupCode']
            groupCode = groupCode.upper()
        except (KeyError, ValueError):
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        try:
            groupObject = Group.objects.get(groupCode=groupCode)
        except ObjectDoesNotExist:
            return JsonResponse(BAD_REQUEST_400(message='invalid group code', data={}), status=400)
        returnValue = {
            "code": groupObject.groupCode,
            "userList": []
        }
        userObjects = groupObject.user.all()
        for userObject in userObjects:
            userStudyTimeInfo = {
                "name": userObject.username,
                "email": userObject.email,
                "profileImg": userObject.profileImgURL,
                "todayStudyTime": 0,
                "isItOwner": True if userObject == groupObject.leaderUser else False,
                "rank": 0
            }
            try:
                userStudyTimeInfo["todayStudyTime"] = Daily.objects.get(userInfo=userObject, date=datetime.now().date())
            except ObjectDoesNotExist:
                pass
            returnValue["userList"].append(userStudyTimeInfo)
        returnValue["userList"] = sorted(returnValue["userList"], key=itemgetter('todayStudyTime'))
        _temp = 0
        while True:
            try:
                returnValue["userList"][_temp]["rank"] = _temp + 1
                _temp += 1
            except (KeyError, ValueError, IndexError):
                break
        return JsonResponse(OK_200(data=returnValue), status=200)


@method_decorator(csrf_exempt, name='dispatch')
class groupUserAPI(APIView):
    def put(self, request):
        if not request.user.is_authenticated or request.user.is_anonymous:
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        try:
            groupCode = request.query_params['groupCode']
            groupCode = groupCode.upper()
        except (KeyError, ValueError):
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        try:
            groupObject = Group.objects.get(groupCode=groupCode)
        except ObjectDoesNotExist:
            return JsonResponse(BAD_REQUEST_400(message='invalid group code', data={}), status=400)
        try:
            groupObject.user.get(email=request.user.email)
            return JsonResponse(CUSTOM_CODE(status=409, message='Already joind group', data={}), status=409)
        except ObjectDoesNotExist:
            pass
        groupObject.user.add(request.user)
        groupObject.userCount += 1
        groupObject.save()
        return JsonResponse(OK_200(data={"code": groupObject.groupCode}), status=200)

    def delete(self, request):
        if not request.user.is_authenticated or request.user.is_anonymous:
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        try:
            groupCode = request.query_params['groupCode']
            groupCode = groupCode.upper()
        except (KeyError, ValueError):
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        try:
            groupObject = Group.objects.get(groupCode=groupCode)
        except ObjectDoesNotExist:
            return JsonResponse(BAD_REQUEST_400(message='There is no Group', data={}), status=400)
        try:
            groupObject.user.get(email=request.user)
        except ObjectDoesNotExist:
            return JsonResponse(BAD_REQUEST_400(message='There is no Group', data={}), status=400)
        if groupObject.leaderUser == request.user:
            return JsonResponse(BAD_REQUEST_400(message="Cannot Exit", data={}), status=400)
        groupObject.user.remove(request.user)
        groupObject.userCount -= 1
        return JsonResponse(OK_200(data={}), status=200)


@method_decorator(csrf_exempt, name='dispatch')
class groupUserManageAPI(APIView):
    def delete(self, request):
        if not request.user.is_authenticated or request.user.is_anonymous:
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        try:
            userToBeDeleted = request.query_params['userMail']
            groupCode = request.query_params['groupCode']
            groupCode = groupCode.upper()
        except (KeyError, ValueError):
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        try:
            groupObject = Group.objects.get(groupCode=groupCode)
        except ObjectDoesNotExist:
            return JsonResponse(CUSTOM_CODE(status=409, message='There is no Group', data={}), status=409)
        if groupObject.leaderUser == userToBeDeleted:
            return JsonResponse(CUSTOM_CODE(status=409, message='Cannot Exit', data={}), status=409)
        if not groupObject.leaderUser == request.user:
            return JsonResponse(CUSTOM_CODE(status=401, message='Unauthorized', data={}), status=401)
        try:
            groupObject.user.get(email=userToBeDeleted)
        except ObjectDoesNotExist:
            return JsonResponse(CUSTOM_CODE(status=404, message='User not found', data={}), status=404)
        groupObject.user.remove(userToBeDeleted)
        groupObject.userCount -= 1
        groupObject.save()
        return JsonResponse(OK_200(data={"code": groupObject.groupCode}), status=200)


@method_decorator(csrf_exempt, name='dispatch')
class postAPI(APIView):
    def post(self, request):
        if not request.user.is_authenticated or request.user.is_anonymous:
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        try:
            _dateStart = request.data['startDate']
            _dateEnd = request.data['endDate']
            calendarType = request.data['calendarType']
            _dateStart = _dateStart.split('-')
            _dateEnd = _dateEnd.split('-')
            try:
                year = int(_dateStart[0])
                month = int(_dateStart[1])
                day = int(_dateStart[2])
                _dateStart = date(year, month, day)
                year = int(_dateEnd[0])
                month = int(_dateEnd[1])
                day = int(_dateEnd[2])
                _dateEnd = date(year, month, day)
            except (IndexError, TypeError):
                return JsonResponse(BAD_REQUEST_400(message='invalid date given', data={}), status=400)
        except (KeyError, ValueError):
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        if _dateStart >= _dateEnd or _dateEnd > datetime.now().date():
            return JsonResponse(BAD_REQUEST_400(message='invalid date given', data={}), status=400)
        postObject = post(
            author=request.user,
            startDate=_dateStart,
            endDate=_dateEnd,
            calendarType=calendarType,
        )
        postObject.save()
        return JsonResponse(OK_200(data={"pk": postObject.primaryKey}), status=200)

    def delete(self, request):
        if not request.user.is_authenticated or request.user.is_anonymous:
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        try:
            primaryKey = request.query_params['pk']
        except (KeyError, ValueError):
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        try:
            postObject = post.objects.get(primaryKey=primaryKey)
        except ObjectDoesNotExist:
            return JsonResponse(BAD_REQUEST_400(message='No Exiting Post', data={}), status=400)
        if not postObject.author == request.user:
            return JsonResponse(BAD_REQUEST_400(message='No Permission to Delete', data={}), status=400)
        else:
            postObject.delete()
            return JsonResponse(OK_200(data={}), status=200)

    def get(self, request):
        try:
            primaryKey = request.query_params['pk']
            pkExists = True
            try:
                postObjects = post.objects.get(primaryKey=primaryKey)
                postObjects = list(postObjects)
            except ObjectDoesNotExist:
                return JsonResponse(BAD_REQUEST_400(message='No Exiting Post', data={}), status=400)
        except (KeyError, ValueError):
            pkExists = False
            postObjects = post.objects.get().order_by('postTime')
        returnValue = {}
        if not pkExists:
            returnValue = {"post": []}
        for postObject in postObjects:
            _dateStart = postObject.startDate
            _dateEnd = postObject.endDate
            stepDate = _dateStart
            achievement = list()
            while stepDate <= _dateEnd:
                dailyAchievement = 0.0
                dailyStudyTime = 0
                try:
                    dateObject = Daily.objects.get(userInfo=postObject.author, date=stepDate)
                    dailyGoal = dateObject.goal
                except ObjectDoesNotExist:
                    achievement.append(dailyAchievement)
                    stepDate += timedelta(days=1)
                    continue
                subjectObjects = dailySubject.objects.filter(dateAndUser=dateObject)
                subjectObjects = list(subjectObjects)
                if not subjectObjects.__len__():
                    achievement.append(dailyAchievement)
                    stepDate += timedelta(days=1)
                    continue
                else:
                    for _subject in subjectObjects:
                        dailyStudyTime += _subject.time
                    try:
                        dailyAchievement = dailyStudyTime / dailyGoal * 100
                    except ZeroDivisionError:
                        dailyAchievement = 0.0
                    achievement.append(dailyAchievement)
                stepDate += timedelta(days=1)
            if pkExists:
                returnValue = {
                    "username": postObject.author.username,
                    "userImage": postObject.author.profileImgURL,
                    "postDate": postObject.postTime.day(),
                    "startDate": postObject.startDate,
                    "endDate": postObject.endDate,
                    "achievementRate": achievement,
                    "calendarType": postObject.calendarType,
                    "like": postObject.likeCount,
                    "idx": postObject.primaryKey
                }
            else:
                subjectDict = {
                    "username": postObject.author.username,
                    "userImage": postObject.author.profileImgURL,
                    "postDate": postObject.postTime.day(),
                    "startDate": postObject.startDate,
                    "endDate": postObject.endDate,
                    "achievementRate": achievement,
                    "calendarType": postObject.calendarType,
                    "like": postObject.likeCount,
                    "idx": postObject.primaryKey
                }
                returnValue["post"].append(subjectDict)
        return JsonResponse(OK_200(data=returnValue), status=200)

