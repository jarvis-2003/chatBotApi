import requests
import json
url = "https://graph.facebook.com/v22.0/807593585770512/messages"
headers = {
    "Authorization": "Bearer EAASekcuBmyABPmG9VdDjrQZBCIZBaOG1qwmpL9lgBAS4hFd30bFB9I7wcL2ayRe68R42mk0WNtuOcfGbQLCuHZCO3Yn7qLp0OOqr27wLQa9ypxXEO6hLZAywZAV52U0mweW5YtbMpdsqTGoAwZAy8iqHAp6EPMFtJgKsZB8MjQRHlmLimyOZBouNrX7q7rM1nVQNroazzJqZANLZBwxzmZAfsrmAyMoGqZBXEppOItti6wXyyIhFYQZDZD",
    "Content-Type": "application/json"
}
def send_message(to,text,options,ButtonText = None):
    if options is None:
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": "91"+to,
            "type": "text",
            "text": {
            "preview_url": False,
            "body": text
            }
        }
    else:
        options_button = []
        if len(options) < 3:
            for index , option in enumerate(options):
                each_option = {
                    "type":"reply",
                    "reply":{
                        "id": f"option_{index+1}",
                        "title":option
                    }
                }
                options_button.append(each_option)
            print(options_button)
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": "91" + to,
                "type": "interactive",
                "interactive":{
                    "type": "button",
                    "body":{"text": text},
                    "footer":{"text":"Please Choose From The Option Below"},
                    "action": {"buttons":options_button}
                }
            }
        else:
            for index , option in enumerate(options):
                each_row = {"id":f"location_{index+1}","title":option}
                options_button.append(each_row)
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": "91" + to,
                "type": "interactive",
                "interactive":{
                    "type": "list",
                    "header":{"type":"text","text":"Choose from the Option"},
                    "body":{"text": text},
                    "footer":{"text":"Please Choose From The Option Below"},
                    "action": {"button":ButtonText,"sections":[{
                        "title": ButtonText,
                        "rows":options_button
                    }]}
                }
            }

    response = requests.post(url,headers=headers,json=payload)
    return response