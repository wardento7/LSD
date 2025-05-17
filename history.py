from fastapi import Depends, HTTPException, APIRouter, status, Request, Query, Response
from sqlalchemy.orm import Session
from database import get_db
import model, oauth,utils, schema
from datetime import datetime
from typing import Optional
import base64
router = APIRouter()
@router.get("/return-data")
async def return_data(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    current_user = oauth.verify_token_access(token, credentials_exception)
    records = db.query(model.Cow).filter(model.Cow.user_id == current_user.user_id).all()
    if not records:
        raise HTTPException(status_code=404, detail="No data")
    result = []
    for record in records:
        image_base64 = None
        if record.image_data:
            try:
                image_base64 = utils.encode_image_to_base64(record.image_data)
            except Exception:
                pass 
        result.append({
            record.id,
            image_base64,
            record.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        })
    return result
@router.post("/confirm-delete/{record_id}")
async def confirm_delete(
    record_id: int,
    confirmation_request: schema.ConfirmationRequest,
    request: Request = None,
    db: Session = Depends(get_db)
):
    confirmation = confirmation_request.confirmation
    if not confirmation:
        return Response(status_code=status.HTTP_400_BAD_REQUEST)
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    current_user = oauth.verify_token_access(token, credentials_exception)
    record = db.query(model.Cow).filter(
        model.Cow.id == record_id,
        model.Cow.user_id == current_user.user_id
    ).first()
    if not record:
        raise HTTPException(status_code=404)
    try:
        db.delete(record)
        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception:
        db.rollback()
        return Response(status_code=500)
@router.get("/search")
async def search_records(
    id: Optional[int] = None,
    query: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    request: Request = None,
    db: Session = Depends(get_db)
):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    current_user = oauth.verify_token_access(token, credentials_exception)
    base_query = db.query(model.Cow).filter(model.Cow.user_id == current_user.user_id)
    if id:
        base_query = base_query.filter(model.Cow.id == id)
    if query:
        base_query = base_query.filter(model.Cow.analysis_result.ilike(f"%{query}%"))
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
            base_query = base_query.filter(model.Cow.created_at >= start_date_obj)
        except ValueError:
            return Response(status_code=400)
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
            base_query = base_query.filter(model.Cow.created_at <= end_date_obj)
        except ValueError:
            return Response(status_code=400) 
    all_records = base_query.all()
    result = []
    for record in all_records:
        if not record.image_data:
            continue 
        try:
            image_base64 = base64.b64encode(record.image_data).decode('utf-8')
        except Exception:
            continue 
        result.append({
            record.id,
            image_base64,
            record.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        })
    return {"data": result}
@router.get("/batch")
async def get_batch_records(
    batch_size: int = Query(10, description="Number of records per batch"),
    offset: int = Query(0, description="Offset for pagination"),
    cow_id: int = Query(None, description="Filter by specific cow ID"),
    request: Request = None,
    db: Session = Depends(get_db)
):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    current_user = oauth.verify_token_access(token, credentials_exception)
    query = db.query(model.Cow).filter(model.Cow.user_id == current_user.user_id)
    if cow_id is not None:
        query = query.filter(model.Cow.id == cow_id)
    total_records = query.count()
    records = query.offset(offset).limit(batch_size).all()
    result = []
    for record in records:
        image_base64 = None
        if record.image_data:
            try:
                image_base64 = utils.encode_image_to_base64(record.image_data)
            except Exception:
                pass
        result.append({
            record.id,
            image_base64,
            record.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        })
    has_more = (offset + batch_size) < total_records if cow_id is None else False
    return {
         result,
         total_records,
         has_more,
        offset + batch_size if has_more else None
    }