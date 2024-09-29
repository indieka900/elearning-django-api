import random
import string
from django_otp.oath import TOTP
from django_otp.util import random_hex
import time

class OTPManager:
    @staticmethod
    def generate_otp(user):
        secret_key = random_hex(20)  # Generate a random secret key
        totp = TOTP(key=secret_key.encode())  # Create TOTP instance
        totp.digits = 6
        totp.step = 600  # Set interval (300 seconds = 5 minutes)
        totp.time = time.time()
        user.secret = secret_key
        user.save()
        return totp.token()

    @staticmethod
    def verify_otp(user, otp):
        totp = TOTP(key=user.secret.encode())  # Create TOTP instance
        totp.digits = 6
        totp.step = 600
        gentoken = totp.token()
        
        if gentoken == otp:

            return True
        else:
            return False


def generate_password(length):
    characters = string.ascii_letters + string.digits
    password = ''.join(random.choice(characters) for i in range(length))
    return password   