from sqlalchemy.orm import Session
from fastapi import Depends
from database import get_db
from . import model
from sentence_transformers import SentenceTransformer, util
model_pp = SentenceTransformer('distiluse-base-multilingual-cased-v1')
def delete_chat(db: Session, id: int, user_id: int):
    try:
        chat = db.query(model.Chat).filter(
            model.Chat.chat_id == id,
            model.Chat.user_id == user_id
        ).first()
        if not chat:
            return {"error": "المحادثة غير موجودة"}
        db.delete(chat)
        db.commit()
        return "تم الحذف بنجاح."
    except Exception as e:
        db.rollback()
        return {"error": f"حدث خطأ أثناء حذف المحادثة: {str(e)}"}
def find_best_match(user_question: str, db: Session = Depends(get_db)) -> str:
    try:
        faqs = db.query(model.FAQ).all()
        if not faqs:
            return "عذراً، لا توجد أسئلة في قاعدة البيانات."
        questions = [faq.question for faq in faqs]
        embeddings = model_pp.encode(questions, convert_to_tensor=True)
        user_embedding = model_pp.encode(user_question, convert_to_tensor=True)
        cosine_scores = util.pytorch_cos_sim(user_embedding, embeddings)[0]
        sorted_scores = sorted(
            enumerate(cosine_scores), key=lambda x: x[1], reverse=True
        )
        best_index, best_score = sorted_scores[0][0], sorted_scores[0][1].item()
        second_score = sorted_scores[1][1].item() if len(sorted_scores) > 1 else 0
        if best_score < 0.5 or (best_score - second_score < 0.05):
            return "آسف لا أستطيع الإجابة على سؤالك، جرب سؤالًا آخر 🐮💬"
        return faqs[best_index].answer
    except Exception as e:
        return f"حدث خطأ أثناء البحث عن الإجابة: {str(e)}"
def save_chat_to_db(db: Session, user_id: int, message: str, response: str):
    try:
        chat = model.Chat(
            user_id=user_id,
            message=message,
            response=response
        )
        db.add(chat)
        db.commit()
        db.refresh(chat) 
        return chat
    except Exception as e:
        db.rollback() 
        return {"error": f"حدث خطأ أثناء حفظ المحادثة: {str(e)}"}