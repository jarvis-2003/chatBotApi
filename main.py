# the idea thats need to be implemented is this api is not thread safe 
# if multiple user hit the api at same time there is a chance that the answers of multiple user gets collided with each other or it can happen that anyone can update anyones answer
# 
# 
# Solution i have come with is:
# when the user hits the chatbot button then a session id will be generated which will go with the questions to the frontend like for every hit to the /question a new session id will be generated 
# 
# then we can store the session id in the frontend cookies or localstorage or session storage 
# 
# with evry answer given by the user the session id will also come with the answer and looking at the session id Answers will be pushed to the respective one.  

from fastapi import FastAPI
from pydantic import BaseModel
from pymongo import MongoClient
from dotenv import load_dotenv
import os


app = FastAPI()

answers = {};

class Question(BaseModel):
    text: str
    type: str
    options: list[str]
    name: str

class Answers(BaseModel):
    name: str
    answer: str

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB_NAME")

# setting up th dataBase client.
client = MongoClient(MONGO_URI) #here the connection with the uri is done
db = client[MONGO_DB] #here the database is loaded
botQuestions = db["botQuestion"]
Records = db["Records"]


@app.get("/questions")
def questions():
    templist = []
    total = botQuestions.count_documents({})
    for x in range(1, total + 1):
        doc = botQuestions.find_one({"sequence": x}, {"_id": 0})
        if doc:
            templist.append(doc)
    return templist

@app.post("/save-answer")
def SaveandFilter(data: Answers):
    total_questions = botQuestions.count_documents({"name": {"$ne": None}})

    # still collecting answers
    if len(answers) + 1 < total_questions:
        if data.name is not None:
            answers[data.name] = data.answer
            print(answers)

    # this is for adding the last record to the answers and saving it to Records
    elif len(answers) + 1 == total_questions:
        if data.name is not None:
            answers[data.name] = data.answer
            print(answers)

        email = answers.get("email")
        phone = answers.get("phone")

        findMail = Records.find_one({"email": email, "phone": phone})
        if not findMail:
            Records.insert_one(answers)
        else:
            Records.update_one({"email": email, "phone": phone}, {"$set": answers})

            # Here the logic of filtering will be written then answers will be cleared.

        answers.clear()
    else:
        return {"error": "All questions already answered"}

#Things left to do 
# 1)Admin api functionality :Update&Delete Records :Add Questions and can Add Property
# 2)Make it Thread safe
# 3)Filter out data and make a pdf using third party application
# 4)Send the PDF as Response to the destined User. 