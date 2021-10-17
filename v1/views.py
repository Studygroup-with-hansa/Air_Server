from rest_framework.views import APIView
from .services.returnStatusForm import *
from .services.randomCharCreator import createRandomChar as randCode
from .services.sendSMTP import send
from datetime import datetime, timedelta

from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.http import HttpRequest, JsonResponse
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
