import cv2
import os
import base64
from passlib.context import CryptContext
import logging
import traceback
from model import Cow
from PIL import Image, ExifTags
import numpy as np
from ultralytics import YOLO
logging.basicConfig(level=logging.INFO, format='🔹 [%(levelname)s] %(message)s')
model_filename = "best.pt"
model_path = os.path.join(os.path.dirname(__file__), model_filename)
logging.info(f"🔄 تحميل الموديل من: {model_path}")
try:
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"❌ Model file '{model_filename}' not found at {model_path}")
    model = YOLO(model_path)
except Exception as e:
    logging.error(f"❌ خطأ أثناء تحميل الموديل: {str(e)}")
    raise
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def hash(password: str) -> str:
    return pwd_context.hash(password)
def verify(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
def auto_orient(frame):
    try:
        pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = pil_img._getexif()
        if exif is not None:
            orientation_value = exif.get(orientation, None)
            if orientation_value == 3:
                pil_img = pil_img.rotate(180, expand=True)
            elif orientation_value == 6:
                pil_img = pil_img.rotate(270, expand=True)
            elif orientation_value == 8:
                pil_img = pil_img.rotate(90, expand=True)
        return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    except Exception as e:
        logging.warning(f"⚠ خطأ في auto-orient: {str(e)}")
        return frame
def resize_frame(frame, size=(640, 640)):
    return cv2.resize(frame, size, interpolation=cv2.INTER_LINEAR)
def auto_adjust_contrast(frame):
    img_yuv = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV)
    img_yuv[:, :, 0] = cv2.equalizeHist(img_yuv[:, :, 0])
    img_output = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR)
    return img_output
def process_frame(frame):
    frame = auto_orient(frame)
    frame = resize_frame(frame, (640, 640))
    frame = auto_adjust_contrast(frame)
    return frame
def process_image(image_path: str, db, current_user):
    try:
        logging.info(f"📷 معالجة الصورة من: {image_path}")
        image = cv2.imread(image_path)
        if image is None:
            return None, "❌ لم يتم العثور على الصورة"
        image = process_frame(image)
        results = model(image)
        detections = []
        for r in results:
            for box in r.boxes:
                detections.append({
                    "class_id": int(box.cls[0]),
                    "confidence": float(box.conf[0]),
                    "bbox": box.xyxy[0].tolist()
                })
        success, buffer = cv2.imencode(".jpg", image)
        if not success:
            return None, "❌ فشل في تحويل الصورة إلى JPG"
        encoded_image = base64.b64encode(buffer).decode("utf-8")
        new_image = Cow(
            user_id=current_user.user_id,
            image_data=base64.b64decode(encoded_image),
            analysis_result=str(detections)
        )
        db.add(new_image)
        db.commit()
        db.refresh(new_image)
        logging.info("✅ تم حفظ الصورة وتحليلها")
        return {
            encoded_image
        }
    except Exception as e:
        logging.error(f"❌ خطأ أثناء معالجة الصورة: {str(e)}")
        logging.error(traceback.format_exc())
        return None, f"حدث خطأ أثناء معالجة الصورة: {str(e)}"
def process_video_store_and_return_encoded(video_path: str, db, current_user):
    try:
        if not os.path.exists(video_path):
            return None, "❌ الفيديو غير موجود"
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None, "❌ لا يمكن فتح الفيديو"
        temp_output = "temp_processed_video.avi"
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        fps = int(cap.get(cv2.CAP_PROP_FPS)) or 20
        width, height = 640, 640
        out = cv2.VideoWriter(temp_output, fourcc, fps, (width, height))
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame_count += 1
            logging.info(f"🎞 فريم رقم {frame_count}")
            frame = process_frame(frame)
            results = model(frame)
            out.write(frame)
        cap.release()
        out.release()
        with open(temp_output, "rb") as f:
            video_bytes = f.read()
        video_base64 = base64.b64encode(video_bytes).decode("utf-8")
        new_entry = Cow(
            user_id=current_user.user_id,
            image_data=base64.b64decode(video_base64),
            analysis_result=f"Processed video with {frame_count} frames"
        )
        db.add(new_entry)
        db.commit()
        db.refresh(new_entry)
        os.remove(temp_output)
        logging.info("✅ تم حفظ الفيديو بعد معالجته")
        return {
            video_base64
        }
    except Exception as e:
        logging.error(f"❌ خطأ أثناء معالجة الفيديو: {str(e)}")
        logging.error(traceback.format_exc())
        return None, f"حدث خطأ أثناء معالجة الفيديو: {str(e)}"