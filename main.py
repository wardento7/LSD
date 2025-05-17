from fastapi import FastAPI
from database import engine, Base
from routers import user, check_cow, history, chatbot
import model
app = FastAPI()
model.Base.metadata.create_all(bind=engine)
app.include_router(user.router)
app.include_router(check_cow.router)
app.include_router(history.router)
app.include_router(chatbot.router)
