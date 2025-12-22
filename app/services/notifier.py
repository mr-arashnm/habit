import random
from kavenegar import KavenegarAPI
from ..config import settings

class Notifier:
    @staticmethod
    def generate_code():
        return str(random.randint(100000, 999999))

    @staticmethod
    def send_sms(phone_number: str, code: str):
        print(f"📧 [EMAIL] Sending code {code} to {phone_number}")
        try:
            api = KavenegarAPI(settings.KAVENEGAR_API_KEY)
            params = {'receptor': phone_number, 'template': settings.OTP_TEMPLATE, 'token': code}
            api.verify_lookup(params)
            return True
        except Exception as e:
            print(f"SMS Error: {e}")
            return False

    @staticmethod
    def send_email(email: str, code: str):
        # در اینجا می‌توانید از fastapi-mail یا هر سرویس SMTP استفاده کنید
        print(f"📧 [EMAIL] Sending code {code} to {email}")
        return True