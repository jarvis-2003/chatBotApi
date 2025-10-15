import re,smtplib
from route.user_routes import generate_secure_otp
from database import Records
from email.mime.text import MIMEText
import os
from utils.stateandcity import stateandcity
from rapidfuzz import process,fuzz
from utils.send_wpmessages import send_message

def checkEmail(answer):
    regex_email = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(regex_email,answer):
        status = otpgenerator(answer)
        return status
    else:
        return False

def otpgenerator(email):
    findMail = Records.find_one({"email" : email})
    if not findMail:
        otp = generate_secure_otp()
        msg = MIMEText(f"Your verication OTP is : {otp}")
        msg['Subject'] = "Your OTP code"
        msg['From'] = "sms.alert069@gmail.com"
        msg['To'] = email.strip()

        server = smtplib.SMTP('smtp.gmail.com',587)
        try:
            server.starttls()
            server.login('sms.alert069@gmail.com', os.getenv("APP_PASSWORD"))
            server.sendmail("sms.alert069@gmail.com",email.strip(),msg.as_string())
            return {"status":"success" , "otp":otp}
        except Exception as e:
            return {"status":"failed"}
        finally:
            server.quit()
    else:
        return {"status" : "verified"}
    
def checklocation(answer,to):
    if answer.strip().lower() in [city.lower() for city in stateandcity["Chhattisgarh"]]:
        return {"status": "success", "location": answer}
    answerscheckwords = re.split(r'[,\s]+',answer)
    words = list(filter(None, answerscheckwords))
    if len(words) == 1:
        location = words[0]
        if location in stateandcity["Chhattisgarh"]:
            return {"status" : "success" , "location": location }
        else:
            stat_obj = fuzzycheck(words[0],stateandcity["Chhattisgarh"])
            if stat_obj:
                if len(stat_obj["location_list"]) > 0:
                    send_message(to,"Inconvinience the entered city didn't match any , please choose from the option",options=stat_obj["location_list"],ButtonText="Do You Mean")
                    return {"status":"pending"}
                else:
                    cities = stateandcity["Chhattisgarh"]
                    text = (
                        "City didn't match any of the cities in Chhattisgarh.\n\n"
                        "Please enter one from the list:\n" +
                        "\n".join(cities)
                    )

                    send_message(to,text=text,options=None)
                    return {"status":"pending"}
    else:
        return {"status":"failed"}

                
def fuzzycheck(checkword,testarray):
    temp = []
    matches = process.extract(checkword.strip().title(),testarray, limit=3 , scorer= fuzz.WRatio)
    for match,score,_ in matches:
        if score > 70:
            temp.append(match)
    print(temp)
    return{"location_list":temp}

def checkBudgetandArea(BudgetOrArea , field ):
    if field.lower() == "budget":
        min = 50000
        max = 200000000
        BudgetOrArea = BudgetOrArea.replace("₹","").replace(" ","")
    else:
        min = 100
        max = 10100
        BudgetOrArea = BudgetOrArea.replace("sqft","").replace(" ","")

    
    pattern = r"^(\d+)(\+)$"
    matchmax = re.match(pattern,BudgetOrArea)
    if matchmax:
        BudgetOrArea = f"{matchmax.group(1)}-{max}"
    regex_budget = r'^\d+\s*-\s*\d+$'
    match = re.match(regex_budget,BudgetOrArea)
    if match:
        token = BudgetOrArea.split("-")
        if int(token[0]) < min or int(token[1]) > max:
            return {"status": "error" , "message" : f"The minimun value is {min} and maximum is {max}. \n Please Enter value between these."}
        else:
            return {"status":"success","value": BudgetOrArea}
    else:
        return{"status":"error","message":f"Please check the input format i.e {min}-{max}"}
    
def sendrangearray(field):
    if field.lower() in ["budget", "squareft"]:
        if field.lower() == "budget":
            min_val = 50000
            max_val = 20000000
            step = 500000   # ₹5 lakh range
            prefix = "₹"
        else:
            min_val = 100
            max_val = 10100
            step = 1000
            prefix = "sqft "

        new_options = []
        current = min_val

        # Generate first 4 range options
        for _ in range(3):
            next_val = current + step
            if next_val >= max_val:
                break
            new_options.append(f"{prefix}{current} - {prefix}{next_val}")
            current = next_val

                # Add the final open-ended option like “2000000+”
        new_options.append(f"{prefix}{current}+")
    return new_options

def addDiscountquestion(message, PhoneNumber, DiscountOption):
    message = message.strip().lower()

    if message == "yes":
        if send_message(PhoneNumber, "Please Enter the Discount Percent You Want ?", DiscountOption,"Select Discount"):
            return {"status": "need_Discount", "answer": [message]}
        else:
            # Even if send_message fails, still return an answer
            return {"status": "error", "answer": message, "error": "Failed to send discount question."}

    elif message == "no":
        return {"status": "normal", "answer": message}

    # Invalid input (not yes/no)
    return {"status": "invalid", "answer": message, "error": "Please choose Yes or No only."}

          
def checkDiscount(message,DiscountOption):
    if message in DiscountOption:
        return True
    return False
