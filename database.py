from sqlalchemy import create_engine 
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:PXMqxNuaVqADcCwuBPNmgBtAvFzjVevJ@yamabiko.proxy.rlwy.net:47483/railway"
engine=create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)
Base = declarative_base()
def get_db():
    db = SessionLocal()
    try:
        print("Database connection is successful")
        yield db
    except Exception as e:
        print(f"Error: {e}")
        raise e
    finally:
        db.close()
        
