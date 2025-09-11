import time ,threading
from route.user_routes import Holdsession
SESSION_TIMEOUT = 1800

def session_cleaner():
    while True:
        now = time.time()
        expired = []
        for key, value in list(Holdsession.items()):
            if (now - value.get("time-stamp", now)) > SESSION_TIMEOUT:
                expired.append(key)

        for each_session in expired:
            print(f"Session : {each_session} expired and removed")
            del Holdsession[each_session]
        time.sleep(120)

print(Holdsession)
cleaner_thread = threading.Thread(target=session_cleaner,daemon=True)