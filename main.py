# make it modular
# handle the db connection differently
# handle the basemodels
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from route import user_routes
from utils.hold_session import cleaner_thread


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"]
)

app.include_router(user_routes.router)
cleaner_thread.start()