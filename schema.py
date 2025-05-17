from pydantic import BaseModel, EmailStr
from typing import Any
from datetime import datetime
class UserCreate(BaseModel):
    user_name: str
    email:EmailStr
    password:str
    class Config:
        from_attributes = True
class UserEmail(BaseModel):
    email: str
    class Config:
        from_attributes = True
class ResetPassword(BaseModel):
    email: str
    otp: str
    new_password: str
    class Config:
        from_attributes = True
class password(BaseModel):
    new_password:str
    confirm_password:str
class TokenData(BaseModel):
    user_id: int
class KResponse(BaseModel):
    image: str 
    result: str 
class ChatMessage(BaseModel):
    message: str
class ChatHistory(BaseModel):
    message: str
    response: str
    timestamp: datetime
class ChatResponse(BaseModel):
    response: str
    class Config:
        from_attributes = True
class Chat(BaseModel):
    message: str
    class Config:
        from_attributes = True
class ConfirmationRequest(BaseModel):
    confirmation: bool
class UsernameChange(BaseModel):
    new_username: str
class EmailChange(BaseModel):
    new_email: EmailStr