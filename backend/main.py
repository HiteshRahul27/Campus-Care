import csv, io
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY   = os.getenv("SECRET_KEY", "change_me_in_production")
ALGORITHM    = "HS256"
TOKEN_EXPIRE = 60 * 8  # 8 hours

engine      = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base        = declarative_base()
pwd_ctx     = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2      = OAuth2PasswordBearer(tokenUrl="/auth/login")

# ── Models ────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"
    id         = Column(Integer, primary_key=True, index=True)
    username   = Column(String(50), unique=True, nullable=False, index=True)
    full_name  = Column(String(100))
    hashed_pw  = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Student(Base):
    __tablename__ = "students"
    id           = Column(Integer, primary_key=True, index=True)
    name         = Column(String(100), nullable=False)
    roll_number  = Column(String(20), unique=True, nullable=False, index=True)
    class_name   = Column(String(20), nullable=False)
    gender       = Column(String(10), nullable=False)
    dob          = Column(Date, nullable=False)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    health_records = relationship("HealthRecord", back_populates="student", cascade="all, delete-orphan")

class HealthRecord(Base):
    __tablename__ = "health_records"
    id           = Column(Integer, primary_key=True, index=True)
    student_id   = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    year         = Column(Integer, nullable=False)
    height       = Column(Float)
    weight       = Column(Float)
    vision_left  = Column(String(10))
    vision_right = Column(String(10))
    hemoglobin   = Column(Float)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    student      = relationship("Student", back_populates="health_records")

Base.metadata.create_all(bind=engine)

# Seed default admin if no users exist
def seed_admin():
    db = SessionLocal()
    try:
        if not db.query(User).first():
            db.add(User(username="admin", full_name="Admin User", hashed_pw=pwd_ctx.hash("admin123")))
            db.commit()
    finally:
        db.close()
seed_admin()

# ── Helpers ───────────────────────────────────────────────────────────────────

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain, hashed): return pwd_ctx.verify(plain, hashed)
def hash_password(pw): return pwd_ctx.hash(pw)

def create_token(username: str):
    return jwt.encode({"sub": username, "exp": datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE)}, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username: raise HTTPException(status_code=401, detail="Bad token")
        user = db.query(User).filter(User.username == username).first()
        if not user: raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token", headers={"WWW-Authenticate": "Bearer"})

# ── Schemas ───────────────────────────────────────────────────────────────────

class LoginReq(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    full_name: Optional[str] = None
    password: str

class UserOut(BaseModel):
    id: int; username: str; full_name: Optional[str]; created_at: datetime
    class Config: from_attributes = True

class StudentIn(BaseModel):
    name: str; roll_number: str; class_name: str; gender: str; dob: str

class StudentUpdate(BaseModel):
    name: Optional[str]=None; roll_number: Optional[str]=None
    class_name: Optional[str]=None; gender: Optional[str]=None; dob: Optional[str]=None

class HealthIn(BaseModel):
    student_id: int; year: int
    height: Optional[float]=None; weight: Optional[float]=None
    vision_left: Optional[str]=None; vision_right: Optional[str]=None; hemoglobin: Optional[float]=None

class HealthUpdate(BaseModel):
    year: Optional[int]=None
    height: Optional[float]=None; weight: Optional[float]=None
    vision_left: Optional[str]=None; vision_right: Optional[str]=None; hemoglobin: Optional[float]=None

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(title="School Health API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# ── Auth ──────────────────────────────────────────────────────────────────────

@app.post("/auth/login")
def login(payload: LoginReq, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.hashed_pw):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": create_token(user.username), "token_type": "bearer",
            "user": {"id": user.id, "username": user.username, "full_name": user.full_name}}

@app.get("/auth/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)): return user

# ── Users (admin manages health workers) ─────────────────────────────────────

@app.get("/users/", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(User).all()

@app.post("/users/", response_model=UserOut, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(400, f"Username '{payload.username}' already taken")
    u = User(username=payload.username, full_name=payload.full_name, hashed_pw=hash_password(payload.password))
    db.add(u); db.commit(); db.refresh(u); return u

@app.delete("/users/{uid}", status_code=204)
def delete_user(uid: int, db: Session = Depends(get_db), me=Depends(get_current_user)):
    u = db.query(User).filter(User.id == uid).first()
    if not u: raise HTTPException(404, "User not found")
    if u.id == me.id: raise HTTPException(400, "Cannot delete yourself")
    db.delete(u); db.commit()

# ── Students ──────────────────────────────────────────────────────────────────

@app.get("/students/")
def list_students(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(Student).order_by(Student.class_name, Student.roll_number).all()

@app.post("/students/", status_code=201)
def create_student(payload: StudentIn, db: Session = Depends(get_db), _=Depends(get_current_user)):
    if db.query(Student).filter(Student.roll_number == payload.roll_number).first():
        raise HTTPException(400, f"Roll '{payload.roll_number}' already exists")
    s = Student(**payload.model_dump()); db.add(s); db.commit(); db.refresh(s); return s

@app.put("/students/{sid}")
def update_student(sid: int, payload: StudentUpdate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    s = db.query(Student).filter(Student.id == sid).first()
    if not s: raise HTTPException(404, "Student not found")
    for k, v in payload.model_dump(exclude_unset=True).items(): setattr(s, k, v)
    db.commit(); db.refresh(s); return s

@app.delete("/students/{sid}", status_code=204)
def delete_student(sid: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    s = db.query(Student).filter(Student.id == sid).first()
    if not s: raise HTTPException(404, "Student not found")
    db.delete(s); db.commit()

# ── Health Records ────────────────────────────────────────────────────────────

@app.get("/health-records/")
def list_records(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(HealthRecord).order_by(HealthRecord.year.desc()).all()

@app.post("/health-records/", status_code=201)
def create_record(payload: HealthIn, db: Session = Depends(get_db), _=Depends(get_current_user)):
    if not db.query(Student).filter(Student.id == payload.student_id).first():
        raise HTTPException(404, "Student not found")
    r = HealthRecord(**payload.model_dump()); db.add(r); db.commit(); db.refresh(r); return r

@app.put("/health-records/{rid}")
def update_record(rid: int, payload: HealthUpdate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    r = db.query(HealthRecord).filter(HealthRecord.id == rid).first()
    if not r: raise HTTPException(404, "Record not found")
    for k, v in payload.model_dump(exclude_unset=True).items(): setattr(r, k, v)
    db.commit(); db.refresh(r); return r

@app.delete("/health-records/{rid}", status_code=204)
def delete_record(rid: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    r = db.query(HealthRecord).filter(HealthRecord.id == rid).first()
    if not r: raise HTTPException(404, "Record not found")
    db.delete(r); db.commit()

# ── CSV Export ────────────────────────────────────────────────────────────────

@app.get("/export/csv")
def export_csv(db: Session = Depends(get_db), _=Depends(get_current_user)):
    students = db.query(Student).order_by(Student.class_name, Student.roll_number).all()
    records  = db.query(HealthRecord).all()
    latest   = {}
    for r in records:
        if r.student_id not in latest or r.year > latest[r.student_id].year:
            latest[r.student_id] = r
    out = io.StringIO()
    w   = csv.writer(out)
    w.writerow(["ID","Name","Roll No","Class","Gender","DOB","Year","Height(cm)","Weight(kg)","Hemoglobin(g/dL)","Vision L","Vision R"])
    for s in students:
        r = latest.get(s.id)
        w.writerow([s.id,s.name,s.roll_number,s.class_name,s.gender,str(s.dob),
                    r.year if r else "",r.height if r else "",r.weight if r else "",
                    r.hemoglobin if r else "",r.vision_left if r else "",r.vision_right if r else ""])
    out.seek(0)
    return StreamingResponse(iter([out.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition":"attachment; filename=health_export.csv"})

@app.get("/")
def root(): return {"status": "School Health API running"}
