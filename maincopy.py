from fastapi import FastAPI,Header
from pydantic import BaseModel
from pymongo import MongoClient
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import os , uuid
import json
from rapidfuzz import process,fuzz


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"]
)

Holdsession = {};

with open("state_city.json", "r") as file:
    stateandcity = json.load(file)

class Answers(BaseModel):
    session_id: str
    name: str
    answer: str

class fuzzycheck(BaseModel):
    locations: str
    loclist : list[str]

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB_NAME")

# setting up th dataBase client.
client = MongoClient(MONGO_URI)
db = client[MONGO_DB]

Records = db["Records"]


@app.get("/questions")
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
    botQuestions = db["botQuestion"]
    Get_session_id = data.session_id
    if Get_session_id not in Holdsession:
        return{"error":"Invalid session_id or has expired"}
    total_questions = botQuestions.count_documents({"name": {"$ne": None}})

    # still collecting answers
    if len(Holdsession[Get_session_id]["answers"]) + 1 < total_questions:
        if data.name is not None:
            # logic for validations
            if data.name.lower() == "location":
                location = data.answer.split(",")
                temploclist = []
                for x in location:
                    temploclist.append(x.strip().title())
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
                elif data.answer.strip().title() in stateandcity.keys():
                    state = data.answer.strip().title()
                    options = stateandcity[state]
                    return {"status":"need_city" , "next_question": f"Please Provide a city in {state}" , "optionsAndanswer":{"answer":state ,"city_options": options}}
                # case 3 if the user only provides the city["city"]
                else:
                    city = data.answer.strip().title()
                    # logic for getting the key value from the cities
                    matching_states = []
                    for key,value in stateandcity.items():
                        if city.lower() in [c.lower() for c in value]:
                            matching_states.append(key)
                    if len(matching_states) == 1:
                        Holdsession[Get_session_id]["answers"][data.name.lower()] = f"{matching_states[0]},{city}"
                        return {"status": "saved", "location": f"{matching_states[0]},{city}"}
                    elif len(matching_states) > 1:
                        return {"status" : "need_state" , "next_question": f"Please choose the state for {city}" , "optionsAndanswer":{
                            "answer" : city , "state_option":matching_states
                        }}
                    else:
                        return {
                            "error":f"Try again with a valid city/state in India"
                        }
            if data.name.lower() != "location":
                Holdsession[Get_session_id]["answers"][data.name.lower()] = data.answer
                print(Holdsession)
                return {"status": "saved"}

    # this is for adding the last record to the answers and saving it to Records
    elif len(Holdsession[Get_session_id]["answers"]) + 1 == total_questions:
        if data.name is not None:
            if data.name.lower():
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
        return {"status": "saved"}
    else:
        return {"error": "All questions already answered"}

@app.post("/rapidfuzzy")
def locationcheck(data: fuzzycheck):
    all_cities = []
    for key , value in stateandcity.items():
        for x in value:
            all_cities.append(x)
    temp = []
    matches = process.extract(data.locations, data.loclist , limit = 3 , scorer=fuzz.WRatio)
    for match,score,_ in matches:
        if score > 50:
            temp.append(match)
    return {"expected_cities":temp}

    
    

#Things left to do 
# 1)Admin api functionality :Update&Delete Records :Add Questions and can Add Property
# 2)Make it Thread safe  :done
# 3)Filter out data and make a pdf using third party application
# 4)Send the PDF as Response to the destined User.