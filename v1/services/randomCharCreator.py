import string
import random

def createRandomChar(length):
    string_pool = string.ascii_letters + string.digits
    result = ""
    for i in range(length):
        result += random.choice(string_pool)

    return result
