from fastapi import UploadFile, File, APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
import schema, utils, oauth
from database import get_db
import os
import uuid
router = APIRouter()
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv"}
@router.post("/process-media")
async def process_and_save_media(
    media: UploadFile = File(...),
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
    temp_path = None
    try:
        current_user = oauth.verify_token_access(token, credentials_exception)
        file_extension = os.path.splitext(media.filename)[1].lower()
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        temp_path = f"temp_{unique_filename}"
        with open(temp_path, "wb") as buffer:
            content = await media.read()
            buffer.write(content)
        if file_extension in IMAGE_EXTENSIONS:
            processed_base64, analysis_result = utils.process_image(temp_path, db, current_user)
        elif file_extension in VIDEO_EXTENSIONS:
            processed_base64, analysis_result = utils.process_video_store_and_return_encoded(temp_path, db, current_user)
        else:
            raise HTTPException(status_code=400, detail="Unsupported media format")
        if not processed_base64:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=analysis_result)
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return {
            processed_base64
        }
    except Exception as e:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
