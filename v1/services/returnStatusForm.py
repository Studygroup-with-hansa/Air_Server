def CUSTOM_CODE(status=200, data={}, message='message'):
    STATUS_FORM = {
        "status": status,
        "detail": message,
        "data": data
    }
    return STATUS_FORM

def OK_200(data={}):
    return CUSTOM_CODE(status=200, message='OK', data=data)

def BAD_REQUEST_400(data={}, message='Bad request'):
    return CUSTOM_CODE(status=400, message=message, data=data)

def INVALID_TOKEN():
    STATUS_FORM = {
        "status": 401,
        "detail": "Invalid token.",
        "data": {}
    }
    return STATUS_FORM
