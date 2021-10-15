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
            send(code, email)
            authModel = emailAuth(
                mail=email,
                authCode=code
            )
            authModel.save()
            return JsonResponse(OK_200(data={"isEmailExist": False, "emailSent": True}), status=200)

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
            return JsonResponse(CUSTOM_CODE(status=401, message='invalid auth code', data={"token": ""}))
        validTimeChecker = timezone.now() - timedelta(minutes=5)
        if authTime < validTimeChecker:
            return JsonResponse(CUSTOM_CODE(status=410, message='time limit exceeded(5min)', data={"token": ""}))

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
    def put(self, request):
        try:
            newName = request.data['name']
        except (KeyError, ValueError):
            return JsonResponse(BAD_REQUEST_400(message='Some Values are missing'), status=400)


