from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status, Response
from sqlalchemy.orm import Session
from LSD import model, schema, oauth
from LSD.database import get_db
from LSD.utils_chat import  find_best_match, save_chat_to_db,delete_chat
router = APIRouter()
@router.post("/chat", response_model=schema.ChatResponse)
async def chat_with_bot(
    message: schema.ChatMessage,
    request: Request = None,
    db: Session = Depends(get_db)
):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    current_user = oauth.verify_token_access(token, credentials_exception)
    response = find_best_match(message.message, db)
    if not response:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    chat = save_chat_to_db(db, current_user.user_id, message.message, response)
    if isinstance(chat, dict) and "error" in chat:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return {
        chat.response,
        chat.timestamp
    }
@router.get("/chat-history", response_model=List[schema.ChatHistory])
async def get_chat_history(request: Request = None, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    current_user = oauth.verify_token_access(token, credentials_exception)
    chats = db.query(model.Chat).filter(
        model.Chat.user_id == current_user.user_id
    ).order_by(model.Chat.timestamp.desc()).all()
    return [
        {
            chat.message,
            chat.response,
            chat.timestamp
        }
        for chat in chats
    ]
@router.delete("/delate-chat/{id}", response_model=str)
async def delete_chat_from_db(id: int, request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    current_user = oauth.verify_token_access(token, credentials_exception)
    result = delete_chat(db, id, current_user.user_id)
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=404)
    return Response(status_code=204)
