import os
from sms77api.Sms77api import Sms77api
from dotenv import load_dotenv

load_dotenv()

client = Sms77api(os.getenv("SMS_API_KEY"))
print(client.sms('+918599842514' , 'hello from me', {'json':True}))