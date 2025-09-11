from fastapi import APIRouter, Header
from rapidfuzz import process,fuzz
from database import db,Records
import uuid , time
from email.mime.text import MIMEText
import os
import secrets,string,smtplib
from dotenv import load_dotenv
from twilio.rest import Client
from models import *
from utils.stateandcity import stateandcity

load_dotenv()

router = APIRouter()

Holdsession = {}

@router.get("/questions")
def questions(session_id: str | None = Header(default=None)):
    print(session_id)
    botQuestions = db["botQuestion"]
    if session_id and session_id in Holdsession:
        templist = []
        total = botQuestions.count_documents({})
        for x in range(1, total + 1):
            doc = botQuestions.find_one({"sequence": x}, {"_id": 0})
            if doc:
                templist.append(doc)
        return {"questionlist":templist , "session_id":session_id}
    else:
        new_session_id = str(uuid.uuid4())
        Holdsession[new_session_id] = {"answers":{},"time-stamp": time.time()} 
        templist = []
        total = botQuestions.count_documents({})
        for x in range(1, total + 1):
            doc = botQuestions.find_one({"sequence": x}, {"_id": 0})
            if doc:
                templist.append(doc)
        return {"questionlist":templist , "session_id":new_session_id}


@router.post("/save-answer")
def SaveandFilter(data: Answers):
    botQuestions = db["botQuestion"]
    Get_session_id = data.session_id
    if Get_session_id not in Holdsession:
        return{"error":"Invalid session_id or has expired"}
    total_questions = botQuestions.count_documents({"name": {"$ne": None}})

    # still collecting answers
    if len(Holdsession[Get_session_id]["answers"]) < total_questions - 1:
        if data.name is not None:
            Holdsession[Get_session_id]["time-stamp"] = time.time()
            # logic for validations
            if data.name.lower() == "location":
                location = data.answer.split(",")
                temploclist = []
                for x in location:
                    temploclist.append(x.strip().title())
                print(temploclist)
                # case 1 if the answer is in format ["state,city"]
                if len(temploclist) == 2:
                    state,city = temploclist
                    if state in stateandcity.keys():
                        if city.lower() in [c.lower() for c in stateandcity[state]]:
                            Holdsession[Get_session_id]["answers"][data.name.lower()] = f"{state},{city}"
                            return {"status" : "saved" , "location":f"{state},{city}"}
                        else:
                            return{"error" : "Invalid state/city combination. Please try again"}
                # case 2 if the answer only contains the state ["state"]
                elif "Chhattisgarh" in stateandcity.keys():
                    options = stateandcity["Chhattisgarh"]
                    return {"status":"need_city", "optionsAndanswer":{"answer":"Chhattishgarh","city_options": options}}
                else:
                                
                        return {"error":f"Try again with a valid city/state in India"}
            if data.name.lower() != "location":
                Holdsession[Get_session_id]["answers"][data.name.lower()] = data.answer
                print(Holdsession)
                return {"status": "saved"}

    # this is for adding the last record to the answers and saving it to Records
    elif len(Holdsession[Get_session_id]["answers"]) == total_questions -1:
        if data.name is not None:
            Holdsession[Get_session_id]["time-stamp"] = time.time()
            if data.name.lower():
                Holdsession[Get_session_id]["answers"][data.name.lower()] = data.answer
                print(Holdsession)

        email = Holdsession[Get_session_id]["answers"].get("email")
        phone = Holdsession[Get_session_id]["answers"].get("phone")


        findMail = Records.find_one({"email": email, "phone": phone})
        if not findMail:
            Records.insert_one(Holdsession[Get_session_id]["answers"])
        else:
            print("hii finally updating")
            Records.update_one({"email": email, "phone": phone}, {"$set": Holdsession[Get_session_id]["answers"]})

            # Here the logic of filtering will be written then answers will be cleared.

        Holdsession[Get_session_id]["answers"].clear()
        return {"status": "saved"}
    else:
        return {"error": "All questions already answered"}

@router.post("/rapidfuzzy")
def locationcheck(data: fuzzycheck):    
    all_cities = []
    for key , value in stateandcity.items():
        for x in value:
            all_cities.append(x)
    temp = []
    matches = process.extract(data.locations.strip().title(), data.loclist , limit = 3 , scorer=fuzz.WRatio)
    for match,score,_ in matches:
        if score > 70:
            temp.append(match)
    return {"expected_cities":temp}

@router.post("/otpgen")
def otpgenrator(data: validateEmailPhone):
        # For email OTP
    if data.email and data.session_id in Holdsession:
        Holdsession[data.session_id]["time-stamp"] = time.time()
        findMail = Records.find_one({"email": data.email})

        if not findMail:
            otp = generate_secure_otp()

            # Store the otp in Holdsession
            Holdsession[data.session_id]["otp_email"] = otp
            Holdsession[data.session_id]["email"] = data.email.strip()

            # Send the otp via email
            msg = MIMEText(f"Your Verification OTP is: {otp}")
            msg['Subject'] = "Your OTP Code"
            msg['From'] = "sms.alert069@gmail.com"
            msg['To'] = data.email.strip()

            server = smtplib.SMTP('smtp.gmail.com', 587)
            try:
                server.starttls()
                server.login('sms.alert069@gmail.com', os.getenv("APP_PASSWORD"))
                server.sendmail("sms.alert069@gmail.com", data.email.strip(), msg.as_string())
                return {"status": "success", "message": f"OTP sent to {data.email.strip()}"}
            except Exception as e:
                return {"error": f"Email not sent: {str(e)}"}
            finally:
                server.quit()
        else:
            Holdsession[data.session_id]["answers"]["email"] = data.email.strip()
            return {"status": True}

    # For phone OTP
    if data.phone and data.session_id in Holdsession:
        Holdsession[data.session_id]["time-stamp"] = time.time()
        findPhone = Records.find_one({"phone": data.phone})

        if not findPhone:
            otp = generate_secure_otp()

            # Store the otp in Holdsession
            Holdsession[data.session_id]["otp_phone"] = otp
            Holdsession[data.session_id]["phone"] = data.phone

            account_sid = os.getenv("ACCOUNT_SID")
            auth_token = os.getenv("AUTH_TOKEN")
            client = Client(account_sid, auth_token)

            reqmessage = f"Your otp for CBH_ChatBOT is {otp}"
            try:
                client.messages.create(
                    to=f"+91{data.phone}",
                    from_="+12182261453",
                    body=reqmessage
                )
                return {"status": "success", "message": f"OTP sent to {data.phone}"}
            except Exception as e:
                return {"error": f"SMS not sent: {str(e)}"}
        else:
            Holdsession[data.session_id]["answers"]["phone"] = data.phone
            return {"status": True}

        

        
@router.get("/validateOtp")
def validateOtp(session_id: str | None = Header(default=None),otp: str | None = Header(default=None)):
    validate = False
    print(f"session id is {session_id}\n otp is:{otp}")
    if session_id in Holdsession:       
        if str(Holdsession[session_id].get("otp_email")) == otp:
            validate = True
            Holdsession[session_id]["answers"]["email"] = Holdsession[session_id].get("email")
            Holdsession[session_id].pop("email",None)
            Holdsession[session_id].pop("otp_email",None)
        elif str(Holdsession[session_id].get("otp_phone")) == otp:
            validate = True
            Holdsession[session_id]["answers"]["phone"] = Holdsession[session_id].get("phone")
            Holdsession[session_id].pop("phone",None)
            Holdsession[session_id].pop("otp_phone",None) 
        return {"status":validate}
    
    
def generate_secure_otp(length=6):
    digits = string.digits
    otp = ""
    for _ in range(length):
        otp += secrets.choice(digits)
    return otp
