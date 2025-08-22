from fastapi import FastAPI,Header
from pydantic import BaseModel
from pymongo import MongoClient
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import os , uuid


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"]
)

Holdsession = {};

class Answers(BaseModel):
    session_id: str
    name: str
    answer: str

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB_NAME")

# setting up th dataBase client.
client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
botQuestions = db["botQuestion"]
Records = db["Records"]


@app.get("/questions")
def questions(session_id: str | None = Header(default=None)):
    print(session_id)
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
        Holdsession[new_session_id] = {"answers":{},"completed":False} 
        templist = []
        total = botQuestions.count_documents({})
        for x in range(1, total + 1):
            doc = botQuestions.find_one({"sequence": x}, {"_id": 0})
            if doc:
                templist.append(doc)
        return {"questionlist":templist , "session_id":new_session_id}


@app.post("/save-answer")
def SaveandFilter(data: Answers):
    Get_session_id = data.session_id
    if Get_session_id not in Holdsession:
        return{"error":"Invalid session_id or has expired"}
    total_questions = botQuestions.count_documents({"name": {"$ne": None}})

    # still collecting answers
    if len(Holdsession[Get_session_id]["answers"]) + 1 < total_questions:
        if data.name is not None:
            # logic for validations
            Holdsession[Get_session_id]["answers"][data.name.lower()] = data.answer
            print(Holdsession)

    # this is for adding the last record to the answers and saving it to Records
    elif len(Holdsession[Get_session_id]["answers"]) + 1 == total_questions:
        if data.name is not None:
            Holdsession[Get_session_id]["answers"][data.name.lower()] = data.answer
            print(Holdsession)

        email = Holdsession[Get_session_id]["answers"].get("email")
        phone = Holdsession[Get_session_id]["answers"].get("phone")

        findMail = Records.find_one({"email": email, "phone": phone})
        if not findMail:
            Records.insert_one(Holdsession[Get_session_id]["answers"])
        else:
            Records.update_one({"email": email, "phone": phone}, {"$set": Holdsession[Get_session_id]["answers"]})

            # Here the logic of filtering will be written then answers will be cleared.

        Holdsession[Get_session_id]["answers"].clear()
    else:
        return {"error": "All questions already answered"}


#Things left to do 
# 1)Admin api functionality :Update&Delete Records :Add Questions and can Add Property
# 2)Make it Thread safe  :done
# 3)Filter out data and make a pdf using third party application
# 4)Send the PDF as Response to the destined User.