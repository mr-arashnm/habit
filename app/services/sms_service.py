import random
from kavenegar import KavenegarAPI, APIException, HTTPException
from ..config import settings

class SMSService:
    @staticmethod
    def generate_code():
        return str(random.randint(10000, 99999))

    @staticmethod
    def send_otp(phone_number: str, code: str):
        try:
            api = KavenegarAPI(settings.KAVENEGAR_API_KEY)
            params = {
                'receptor': phone_number,
                'template': settings.OTP_TEMPLATE_NAME,
                'token': code,
                'type': 'sms',
            }
            # استفاده از متد verify (Lookup) برای ارسال فوق سریع
            response = api.verify_lookup(params)
            return True
        except (APIException, HTTPException) as e:
            # در اینجا خطا را لاگ کن (مثلا در کنسول یا فایل)
            print(f"SMS Error: {e}")
            return False