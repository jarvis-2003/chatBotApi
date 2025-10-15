import time ,threading
from route.user_routes import Holdsession
from route.wattsapp_routes import WpHoldSessions
SESSION_TIMEOUT = 1800

def session_cleaner():
    while True:
        now = time.time()
        expired = []
        expired_wp = []
        for key, value in list(Holdsession.items()):
            if (now - value.get("time-stamp", now)) > SESSION_TIMEOUT:
                expired.append(key)
        for key,value in list(WpHoldSessions.items()):
            if(now - value.get("time-stamp",now)) > SESSION_TIMEOUT:
                expired_wp.append(key)
        for each_session in expired:
            print(f"Session : {each_session} expired and removed")
            del Holdsession[each_session]
        for each_wpsession in expired_wp:
            del WpHoldSessions[each_wpsession]
        time.sleep(120)

print(Holdsession)
cleaner_thread = threading.Thread(target=session_cleaner,daemon=True)