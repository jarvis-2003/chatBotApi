from dotenv import load_dotenv
from database import Records,botQuestions
import os,asyncio
from fastapi import Request,APIRouter
from fastapi.responses import PlainTextResponse
import time
from utils.send_wpmessages import send_message
from utils.wpAnswerCheck import *
router = APIRouter()

load_dotenv()

WpHoldSessions = {}

user_locks = {}

@router.get("/chatWebhook")
def verification(request : Request):
    token  = os.getenv("WP_AUTH_TOKEN")
    parameters = request.query_params
    if (parameters.get("hub.mode") == "subscribe" and parameters.get("hub.verify_token") == token):
        print("token match")
        return PlainTextResponse(parameters.get("hub.challenge"))
    else:
        return "Error: token mismatch"
    
    
@router.post("/chatWebhook")
async def intiateChat(request: Request):
    body = await request.json()
    # print("Incoming :" , body)
    entry = body.get("entry",[])[0]
    changes = entry.get("changes",[])[0]
    value = changes.get("value",{})
    if "messages" in value and "contacts" in value:
        user_wattsapp_name = value["contacts"][0]["profile"]["name"]
        user_wattsapp_number = value["contacts"][0]["wa_id"]

        incoming_message = None
        if value["messages"][0]["type"] == "text":
            incoming_message = value["messages"][0]["text"]["body"]
        elif value["messages"][0]["type"] == "interactive":
            interactive = value["messages"][0]["interactive"]
            if interactive["type"] == "button_reply":
                incoming_message = interactive["button_reply"]["title"]
            elif interactive["type"] == "list_reply":
                incoming_message = interactive["list_reply"]["title"]

        if len(user_wattsapp_number) == 12:
            phone_number = user_wattsapp_number[2:]
        else:
            phone_number = user_wattsapp_number

        lock = get_user_lock(phone_number)
        if lock.locked():
            print(f"User {phone_number} tried sending multiple messages simultaneously.")
            await send_message(phone_number, "⚠️ Please wait, I’m still processing your previous message.", None)
            return "EVENT_RECEIVED"            
        async with lock:
            if  user_wattsapp_number not in WpHoldSessions:
                WpHoldSessions[user_wattsapp_number] = {"answers":{}, "progress": 0 , "time-stamp": time.time() , "conversational_state":"normal"}
            user_session = WpHoldSessions[user_wattsapp_number]

            if user_session["conversational_state"].lower() == "completed":
                if incoming_message.lower() == "reset chat":
                    WpHoldSessions.pop(user_wattsapp_number,None)
                    WpHoldSessions[user_wattsapp_number] = {"answers":{}, "progress": 0 , "time-stamp": time.time() , "conversational_state":"normal"}


            if(user_session["progress"] == 0):
                questionCheck = botQuestions.find_one({"sequence": user_session.get("progress") + 1}, {"_id": 0})
            else:
                questionCheck = botQuestions.find_one({"sequence": user_session.get("progress")}, {"_id": 0})
        
        # for the otp verification 
            if user_session["conversational_state"] == "need_otp":
                req_otp = incoming_message.strip()
                if req_otp == str(user_session.get("email_otp")):
                    user_session["answers"][questionCheck["name"].lower()] = user_session.get("unverified_email")
                    user_session.pop("unverified_email", None)
                    user_session.pop("email_otp", None)
                    user_session["conversational_state"] = "normal"
                    send_message(phone_number,f"✅ Email verified successfully! \n proceeding to next question.",None)
                    user_session["progress"] += 1
                elif req_otp.lower() == "change email":
                    user_session["conversational_state"] = "normal"
                    send_message(phone_number, "Please enter your new email address:", None)
                    return
                elif req_otp.lower() == "resend otp":
                    email_to_resend = user_session.get("unverified_email")
                    if email_to_resend:
                        status = checkEmail(email_to_resend)
                        if status and status.get("status") == "success":
                            user_session["email_otp"] = status.get("otp")
                            res = send_message(phone_number, f"📩 OTP resent to {email_to_resend}! Please check your email.", None)
                    else:
                        res = send_message(phone_number, "⚠️ No email found to resend OTP. Please enter your email again.", None)
                    return
                else:
                    send_message(phone_number,"❌ Invalid OTP. Please try again.",None)
                    return


            if user_session["conversational_state"] == "change_email":
                req_ans = incoming_message.strip().lower()
                match(req_ans):

                    case "change email":
                        user_session["conversational_state"] = "normal"
                        send_message(phone_number, "Please enter your new email address:", None)
                        return
                    case "reset":
                        user_session["conversational_state"] = "normal"
                        user_session["progress"] = 1
                    case _:
                    # default: anything else typed
                        send_message(
                            phone_number,
                            "⚠️ Please reply with *Change Email* or *Reset* to continue.",
                            ["Change Email", "Reset"]
                        )
                        return

            if questionCheck and questionCheck["name"].lower() == "email" and user_session["conversational_state"] == "normal" and not user_session["answers"].get("email"):
                status = checkEmail(incoming_message)
                if status and status.get("status") == "success":
                    user_session["email_otp"] = status.get("otp")
                    user_session["unverified_email"] = incoming_message
                    user_session["conversational_state"] = "need_otp"
                    res = send_message(to=phone_number,text=f"Please Enter the OTP sent to {incoming_message}",options=["Change Email" , "Resend OTP"])
                    return
                elif status and status.get("status") == "failed":
                    user_session["conversational_state"] = "change_email"
                    user_session["unverified_email"] = incoming_message
                    res = send_message(phone_number,f"Something went wrong !! \n\n Please enter a new  email to proceed",["Change Email","Reset"])
                    return
                elif status and status.get("status") == "verified":
                    user_session["conversational_state"] = "normal"
                    user_session["answers"][questionCheck["name"].lower()] = incoming_message
                    res = send_message(phone_number,f" ✅ Mail Id already verified. \n Moving to next Question",None)

                else:
                    res = send_message(phone_number,
                    "❌ Invalid email format. Please enter a valid email to proceed.",
                    None)
                    return "EVENT_RECEIVED"  
            
            if questionCheck and questionCheck["name"].lower() == "location" and user_session["conversational_state"] == "normal" and not user_session["answers"].get("location"):
                stat_loc = checklocation(answer=incoming_message , to=phone_number)
                if stat_loc and stat_loc["status"] == "success":
                    location_answer = stat_loc["location"]
                    user_session["answers"][questionCheck["name"].lower()] = location_answer
                elif stat_loc["status"] == "pending":
                    return
                else:
                    send_message(phone_number,"Please Enter only one valid city from chhattisgarh",options=None)
                    return
                
            if questionCheck and questionCheck["name"].lower() in ["budget","squareft"]:
                budget_stat = checkBudgetandArea(incoming_message,questionCheck["name"].lower())
                if budget_stat and budget_stat["status"] == "error":
                    send_message(phone_number,budget_stat["message"],None)
                    return
                else:
                    incoming_message = budget_stat["value"]

            if questionCheck and questionCheck["name"].lower() == "onetimesettlement" and user_session["conversational_state"] == "normal":
                status = addDiscountquestion(incoming_message,phone_number,["10%","20%","30%"])
                if status and status["status"] == "need_Discount":
                    user_session["conversational_state"] = "need_Discount"
                    user_session["answers"][questionCheck["name"].lower()] = status["answer"]
                    return
                elif status["status"] == "normal":
                    user_session["answers"][questionCheck["name"].lower()] = status["answer"]
                else:
                    send_message(phone_number,status["error"],None)
                    return
            
            if user_session["conversational_state"] == "need_Discount":
                req_answer = incoming_message.strip().lower()
                print("entered here")
                if checkDiscount(req_answer,["10%","20%","30%"]):
                    user_session["conversational_state"] = "normal"
                    user_session["answers"][questionCheck["name"].lower()].append(req_answer)
                    user_session["progress"] += 1
                else:
                    send_message(phone_number,"Please Enter a value from the option given",None)
                    return

            
            old_user = Records.find_one({"phone": int(phone_number)})

            if user_session["progress"] == 0:

                if not incoming_message:
                # no answer, stay on the same question
                    print("⚠️ No answer received. Waiting for user reply.")
                    return
                user_session["time-stamp"]= time.time()
            
                if not old_user:
                    welcome_message = f"Hii {user_wattsapp_name} ,Welcome to Chattishgarh Housing Board Housing Board .\n This is a personalized ChatBot made to get details on the properties in chattishgarh without getting the trouble to navigate through our website.Let's get started without first question."
                else:
                    welcome_message = f"Hello {old_user['name']}, welcome back to Chhattisgarh Housing Board!.🌟\n We’re glad to have you again. Seems like you couldn't complete the last conversation , get the latest properties details here by answering all the questions here ."

                response = send_message(phone_number,welcome_message,None)
                question1 = botQuestions.find_one({"sequence": 1}, {"_id": 0})
                responseQuestion = send_message(phone_number,question1["text"],question1["options"])
                user_session["progress"] = 1
                return "EVENT RECIEVED"
        

            # now fetching the next question based on the progress
            if user_session["progress"] > 0 and user_session["conversational_state"] == "normal":
                questionCheckagain = botQuestions.find_one({"sequence": user_session["progress"]}, {"_id": 0})

                if not incoming_message:
                # no answer, stay on the same question
                    print("⚠️ No answer received. Waiting for user reply.")
                    return
                user_session["time-stamp"] = time.time()

                if questionCheckagain and questionCheckagain["name"].lower() not in ("email","location","phone","onetimesettlement"):
                    user_session["answers"][questionCheckagain["name"].lower()] = incoming_message
                
                next_question = botQuestions.find_one({"sequence": user_session["progress"] + 1}, {"_id": 0})
                while next_question and next_question["name"].lower() == "phone":
                    user_session["progress"] += 1
                    user_session["answers"]["phone"] = int(phone_number)
                    next_question = botQuestions.find_one({"sequence": user_session["progress"]+1}, {"_id": 0})   
                if next_question:
                    if next_question["name"].lower() in ["budget" , "squareft"]:
                        getarray = sendrangearray(next_question["name"].lower())
                        print(getarray)
                        getres = send_message(phone_number,next_question["text"],getarray,f"choose {next_question["name"].lower()}")
                        if getres:
                            user_session["progress"] += 1 
                    else:
                        responseQuestion = send_message(phone_number,next_question["text"],next_question["options"])
                        if responseQuestion:
                            user_session["progress"] += 1
                            print(WpHoldSessions)
                else:
                    if user_session["conversational_state"] != "Completed":
                        completion_message = (
                        "🎉 You’ve successfully answered all the questions!\n\n"
                        "📄 Your personalized PDF report is now being generated. "
                        "This may take a few moments, so please wait patiently.\n\n"
                        "🙏 Thank you for using the Chhattisgarh Housing Board Chatbot. 🏡"
                        )
                        send_message(phone_number,completion_message,None)
                        #filtering logic will be added here then will be marked completed
                        send_message(phone_number,"Start a new chat after 1 hour else reset the chat and start over again",["reset chat"])
                        user_session["conversational_state"] = "Completed"

                if user_session and user_session.get("conversational_state").lower() == "completed":
                    findvar = user_session["answers"]
                    findmail = Records.find_one({"email":findvar.get("email").lower(),"phone": findvar.get("phone").lower()})
                    if not findmail:
                        Records.insert_one(user_session["answers"])
                    else:
                        Records.update_one({"email":findvar.get("email").lower(),"phone":findvar.get("phone").lower()}, {"$set": user_session["answers"]})
                    WpHoldSessions.pop(user_wattsapp_number,None)



 
        return "EVENT_RECIEVED"



def get_user_lock(phone_number: str) -> asyncio.Lock:
    if phone_number not in user_locks:
        user_locks[phone_number] = asyncio.Lock()
    return user_locks[phone_number]
