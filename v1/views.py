import json
from operator import itemgetter

from rest_framework.views import APIView
from .services.returnStatusForm import *
from .services.randomCharCreator import createRandomChar as randCode
from .services.sendSMTP import send
from datetime import datetime, timedelta, date
from .config import config

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
            _dateStart = _dateStart.split('.') if _dateStart.count('.') else _dateStart.split('-')
            _dateEnd = _dateEnd.split('.') if _dateEnd.count('.') else _dateEnd.split('-')
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
            dailyObject = Daily.objects.get(userInfo=request.user, date=datetime.now().date())
            subjectObject = dailySubject.objects.get(dateAndUser=dailyObject, title=subjTitle)
            subjectObject.delete()
        except ObjectDoesNotExist:
            pass
        try:
            subjectDB = userSubject.objects.get(user=request.user, title=subjTitle)
            subjectDB.delete()
            return JsonResponse(OK_200(data={}), status=200)
        except ObjectDoesNotExist:
            return JsonResponse(BAD_REQUEST_400(message="Subject "+subjTitle+" is not exists", data={}), status=400)


    def put(self, request):
        if not request.user.is_authenticated or request.user.is_anonymous:
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        try:
            subjectTitle = request.query_params['title']
        except (KeyError, ValueError):
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        dailyObjectFlag = False
        try:
            dailyObject = Daily.objects.get(userInfo=request.user, date=datetime.now().date())
            subjectObject = dailySubject.objects.get(dateAndUser=dailyObject, title=subjectTitle)
            dailyObjectFlag = True
        except ObjectDoesNotExist:
            pass
        try:
            subjectDB = userSubject.objects.get(user=request.user, title=subjectTitle)
        except ObjectDoesNotExist:
            return JsonResponse(BAD_REQUEST_400(message="Subject " + subjectTitle + " is not exists", data={}), status=400)
        try:
            title_new = request.query_params['title_new']
            subjectDB.title = title_new
            if dailyObjectFlag:
                subjectObject.title = request.query_params['title_new']
        except (KeyError, ValueError):
            pass
        try:
            color_new = request.query_params['color']
            subjectDB.color = color_new
            if dailyObjectFlag:
                subjectObject.title = request.query_params['color']
        except (KeyError, ValueError):
            pass
        subjectDB.save()
        if dailyObjectFlag:
            subjectObject.save()
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
            today = datetime.now().date()
            if _date == today:
                isToday = True
            else:
                isToday = False
        except (KeyError, ValueError):
            _date = datetime.now().date()
            isToday = True
        if not isToday:
            pass
        else:
            try:
                userSubjectList = userSubject.objects.filter(user=request.user)
            except ObjectDoesNotExist:
                return JsonResponse(OK_200(data={"totalTime": 0, "subject": [], "goal": request.user.targetTime}))
            try:
                daily = Daily.objects.get(userInfo=request.user, date=_date)
            except ObjectDoesNotExist:
                daily = Daily(
                    userInfo=request.user,
                    goal=request.user.targetTime,
                )
                daily.save()
            for userSubjectObject in userSubjectList:
                try:
                    _userSubject = dailySubject.objects.get(dateAndUser=daily, title=userSubjectObject.title)
                except ObjectDoesNotExist:
                    _userDailySubject = dailySubject(
                        dateAndUser=daily,
                        title=userSubjectObject.title,
                        color=userSubjectObject.color
                    )
                    _userDailySubject.save()
        try:
            daily = Daily.objects.get(userInfo=request.user, date=_date)
            subjectHistory = dailySubject.objects.filter(dateAndUser=daily)
        except ObjectDoesNotExist:
            return JsonResponse(OK_200(data={"totalTime": 0, "subject": [], "goal": 0}))
        subjectHistory = list(subjectHistory)
        returnValue = {"totalTime": 0, "subject": [], "goal": daily.goal}
        for _subjectHistory in subjectHistory:
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
        try:
            dailyObject = Daily.objects.get(userInfo=request.user, date=datetime.now().date())
            dailyObject.goal = int(time)
            dailyObject.save()
        except ObjectDoesNotExist:
            pass
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
            today = datetime.now().date()
            if _date == today:
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
            today = datetime.now().date()
            if _date == today:
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
                memoDate.memo = str(memoContent)
                memoDate.save()
                return JsonResponse(OK_200(), status=200)
            except ObjectDoesNotExist:
                memoDate = Daily(
                    userInfo=request.user,
                    date=_date,
                    goal=request.user.targetTime,
                    memo=str(memoContent)
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
                                             "time": Daily.objects.get(userInfo=userObject, date=datetime.now().date()).totalStudyTime}
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
                userStudyTimeInfo["todayStudyTime"] = Daily.objects.get(userInfo=userObject, date=datetime.now().date()).totalStudyTime
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
            _dateStart = request.query_params['startDate']
            _dateEnd = request.query_params['endDate']
            calendarType = request.query_params['calendarType']
            _dateStart = _dateStart.split('.') if _dateStart.count('.') else _dateStart.split('-')
            _dateEnd = _dateEnd.split('.') if _dateEnd.count('.') else _dateEnd.split('-')
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
            postObjects = post.objects.all().order_by('postTime')
        returnValue = {}
        if not pkExists:
            returnValue = {"count": 0, "post": []}
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
                try:
                    likeCount = list(like.objects.filter(post=postObject)).__len__()
                except ObjectDoesNotExist:
                    likeCount = 0
                returnValue = {
                    "username": postObject.author.username,
                    "userImage": postObject.author.profileImgURL,
                    "postDate": postObject.postTime.strftime("%Y-%m-%d"),
                    "startDate": postObject.startDate.strftime("%Y-%m-%d"),
                    "endDate": postObject.endDate.strftime("%Y-%m-%d"),
                    "achievementRate": achievement,
                    "calendarType": postObject.calendarType,
                    "like": likeCount,
                    "idx": postObject.primaryKey
                }
            else:
                try:
                    likeCount = list(like.objects.filter(post=postObject)).__len__()
                except ObjectDoesNotExist:
                    likeCount = 0
                subjectDict = {
                    "username": postObject.author.username,
                    "userImage": postObject.author.profileImgURL,
                    "postDate": postObject.postTime.strftime("%Y-%m-%d"),
                    "startDate": postObject.startDate.strftime("%Y-%m-%d"),
                    "endDate": postObject.endDate.strftime("%Y-%m-%d"),
                    "achievementRate": achievement,
                    "calendarType": postObject.calendarType,
                    "like": likeCount,
                    "idx": postObject.primaryKey
                }
                returnValue["count"] += 1
                returnValue["post"].append(subjectDict)
        return JsonResponse(OK_200(data=returnValue), status=200)


@method_decorator(csrf_exempt, name='dispatch')
class postCommentAPI(APIView):
    def post(self, request):
        if not request.user.is_authenticated or request.user.is_anonymous:
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        try:
            content = request.data['content']
            postIdx = request.data['idx']
        except (KeyError, ValueError):
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        try:
            postObject = post.objects.get(primaryKey=postIdx)
        except ObjectDoesNotExist:
            return JsonResponse(BAD_REQUEST_400(message='No Exiting post', data={}), status=400)
        commentObject = comment(
            post=postObject,
            author=request.user,
            content=content
        )
        commentObject.save()
        return JsonResponse(OK_200(data={"pk": commentObject.primaryKey}), status=200)

    def delete(self, request):
        if not request.user.is_authenticated or request.user.is_anonymous:
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        try:
            commentPK = request.query_params['pk']
        except (KeyError, ValueError):
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        try:
            commentObject = comment.objects.get(primaryKey=commentPK)
        except ObjectDoesNotExist:
            return JsonResponse(BAD_REQUEST_400(message='No Exiting comment', data={}), status=400)
        if commentObject.author == request.user:
            commentObject.delete()
            return JsonResponse(OK_200(data={}), status=200)
        else:
            return JsonResponse(CUSTOM_CODE(status=401, data={}, message='No Permission to Delete'), status=401)

    def get(self, request):
        if not request.user.is_authenticated or request.user.is_anonymous:
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        try:
            postPK = request.query_params['pk']
        except (KeyError, ValueError):
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        try:
            postObject = post.objects.get(primaryKey=postPK)
        except ObjectDoesNotExist:
            return JsonResponse(BAD_REQUEST_400(message='No Exiting post', data={}), status=400)
        returnValue = {"count": 0, "comments": []}
        try:
            commentObjects = comment.objects.filter(post=postObject)
        except ObjectDoesNotExist:
            return JsonResponse(OK_200(data=returnValue), status=200)
        commentObjects = commentObjects.order_by('postTime')
        commentObjects = list(commentObjects)
        for commentObject in commentObjects:
            commentDataForm = {
                "username": commentObject.author.username,
                "userImage": commentObject.author.profileImgURL,
                "postDate": commentObject.postTime.date().strftime("%Y-%m-%d"),
                "content": commentObject.content,
                "idx": commentObject.primaryKey
            }
            returnValue["count"] += 1
            returnValue["comments"].append(commentDataForm)
        return JsonResponse(OK_200(data=returnValue), status=200)


@method_decorator(csrf_exempt, name='dispatch')
class postLikeAPI(APIView):
    def post(self, request):
        if not request.user.is_authenticated or request.user.is_anonymous:
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        try:
            postPK = request.query_params['pk']
        except (KeyError, ValueError):
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        try:
            postObject = post.objects.get(primaryKey=postPK)
        except ObjectDoesNotExist:
            return JsonResponse(BAD_REQUEST_400(message='No Exiting post', data={}), status=400)
        try:
            likeObject = like.objects.get(user=request.user, post=postObject)
            likeObject.delete()
            return JsonResponse(OK_200(data={"isChecked": False}), status=200)
        except ObjectDoesNotExist:
            likeObject = like(
                user=request.user,
                post=postObject
            )
            likeObject.save()
            return JsonResponse(OK_200(data={"isChecked": True}), status=200)

    def get(self, request):
        try:
            postPK = request.query_params['pk']
        except (KeyError, ValueError):
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        try:
            postObject = post.objects.get(primaryKey=postPK)
        except ObjectDoesNotExist:
            return JsonResponse(BAD_REQUEST_400(message='No Exiting post', data={}), status=400)
        returnValue = {"user": []}
        try:
            likeObjects = like.objects.filter(post=postObject)
        except ObjectDoesNotExist:
            return JsonResponse(OK_200(data=returnValue), status=200)
        likeObjects = list(likeObjects)
        for likeObject in likeObjects:
            likeDataForm = {
                "email": likeObject.user.email,
                "username": likeObject.user.username
            }
            returnValue["user"].append(likeDataForm)
        return JsonResponse(OK_200(data=returnValue), status=200)


@method_decorator(csrf_exempt, name='dispatch')
class rankAPI(APIView):
    def get(self, request):
        try:
            userDailyObjects = Daily.objects.filter(date=datetime.now().date())
        except ObjectDoesNotExist:
            return JsonResponse(OK_200(data={"rank": []}), status=200)
        userDailyObjects = list(userDailyObjects)
        returnData = {
            "myInfo": {},
            "rank": []
        }
        for userDailySubject in userDailyObjects:
            userForm = {
                "rank": '0',
                "username": userDailySubject.userInfo.username,
                "usermail": userDailySubject.userInfo.email,
                "totalStudyTime": 0,
                "achievementRate": []
            }
            _dateStart = datetime.now().date() - timedelta(days=6)
            _dateEnd = datetime.now().date()
            stepDate = _dateStart
            while stepDate <= _dateEnd:
                dailyAchievement = 0
                dailyStudyTime = 0
                try:
                    dateObject = Daily.objects.get(userInfo=userDailySubject.userInfo, date=stepDate)
                    dailyGoal = dateObject.goal
                except ObjectDoesNotExist:
                    userForm["achievementRate"].append(dailyAchievement)
                    stepDate += timedelta(days=1)
                    continue
                subjectObjects = dailySubject.objects.filter(dateAndUser=dateObject)
                subjectObjects = list(subjectObjects)
                if not subjectObjects.__len__():
                    userForm["achievementRate"].append(dailyAchievement)
                    stepDate += timedelta(days=1)
                    continue
                else:
                    for _subject in subjectObjects:
                        dailyStudyTime += _subject.time
                    try:
                        userForm["totalStudyTime"] += dailyStudyTime
                        dailyAchievement = int(dailyStudyTime / dailyGoal * 100)
                    except ZeroDivisionError:
                        pass
                    userForm["achievementRate"].append(dailyAchievement)
                stepDate += timedelta(days=1)
            returnData["rank"].append(userForm)
        returnData["rank"] = sorted(returnData["rank"], key=itemgetter('totalStudyTime'), reverse=True)
        rank = 1
        for user in range(len(returnData["rank"])):
            returnData["rank"][rank-1]["rank"] = str(rank)
            rank += 1
        myInfo = (item for item in returnData["rank"] if item["usermail"] == request.user.email)
        myInfo = next(myInfo, False)
        returnData["myInfo"] = myInfo if myInfo else {
            "rank": '-',
            "username": request.user.username,
            "usermail": request.user.email,
            "totalStudyTime": 0,
            "achievementRate": []
        }
        return JsonResponse(OK_200(data=returnData), status=200)


@method_decorator(csrf_exempt, name='dispatch')
class init_all_targetTime(APIView):
    def post(self, request):
        if not request.user.is_authenticated or request.user.is_anonymous:
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        if (not request.user.is_superuser) and (not request.user.is_staff):
            return JsonResponse(CUSTOM_CODE(status=401, message='Not Staff User', data={}), status=200)
        try:
            users = User.objects.all()
        except ObjectDoesNotExist:
            return JsonResponse(OK_200(data={}), status=200)
        for user in users:
            user.targetTime = 0
            user.save()
        return JsonResponse(OK_200(data={}), status=200)


@method_decorator(csrf_exempt, name='dispatch')
class setProfileIMG(APIView):
    def post(self, request):
        if not request.user.is_authenticated or request.user.is_anonymous:
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing', data={}), status=400)
        image = request.FILES['image']
        request.user.profileImgURL = image
        request.user.save()
        return JsonResponse(OK_200(), status=200)

    def get(self, request):
        img = request.user.profileImgURL
        return JsonResponse(OK_200(data={"profileImg": img.url}), status=200)
