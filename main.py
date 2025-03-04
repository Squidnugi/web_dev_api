from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, Session, declarative_base, relationship
from pydantic import BaseModel
import os
from typing import List
from datetime import datetime, date


# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")  # Change to your actual DB URL
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define User Model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String, index=True)
    account_type = Column(String, index=True)
    school_id = Column(Integer, ForeignKey('schools.id'), index=True)
    sessions = relationship("Session", foreign_keys="[Session.supervisor_id, Session.client_id]", back_populates="user")

class schools(Base):
    __tablename__ = "schools"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    address = Column(String, index=True)
    city = Column(String, index=True)
    county = Column(String, index=True)
    postcode = Column(String, index=True)
    phone = Column(Integer, index=True)
    website = Column(String, index=True)
    domain = Column(String, unique=True, index=True)
    sessions = relationship("Session", back_populates="school")

class sessions(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey('schools.id'), index=True)
    school = Column(String, index=True)
    supervisor_id = Column(Integer, ForeignKey('users.id'), index=True)
    supervisor_email = Column(String, index=True)
    client_id = Column(Integer, ForeignKey('users.id'), index=True)
    client_email = Column(String, index=True)
    date = Column(Date, index=True)
    additional_info = Column(String, index=True)
    user = relationship("User", foreign_keys=[supervisor_id, client_id], back_populates="sessions")
    school = relationship("schools", back_populates="sessions")

# Create Tables
Base.metadata.create_all(bind=engine)

# Pydantic Schema
class UserCreate(BaseModel):
    email: str
    password: str
    account_type: str
    school_id: str

class SchoolCreate(BaseModel):
    name: str
    address: str
    city: str
    county: str
    postcode: str
    phone: int
    website: str
    domain: str

class SessionCreate(BaseModel):
    school_id: int
    school: str
    supervisor_id: int
    supervisor_email: str
    client_id: int
    client_email: str
    date: date

class UserResponse(UserCreate):
    id: int
    class Config:
        from_attributes = True

class SchoolResponse(SchoolCreate):
    id: int
    class Config:
        from_attributes = True

class SessionResponse(SessionCreate):
    id: int
    class Config:
        from_attributes = True


# Dependency to get DB Session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# FastAPI App
app = FastAPI()

##for users table
@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(email=user.email, password=user.password, account_type=user.account_type)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/{user}", response_model=UserResponse)
def read_user(user: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/users/", response_model=List[UserResponse])
def read_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@app.delete("/users/{user_id}", response_model=UserResponse)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return user

## for school table

@app.post("/schools/", response_model=SchoolResponse)
def create_school(school: SchoolCreate, db: Session = Depends(get_db)):
    db_school = schools(name=school.name, address=school.address, city=school.city, county=school.county, postcode=school.postcode, phone=school.phone, website=school.website, domain=school.domain)
    db.add(db_school)
    db.commit()
    db.refresh(db_school)
    return db_school

@app.get("/schools/", response_model=List[SchoolResponse])
def read_schools(db: Session = Depends(get_db)):
    return db.query(schools).all()

@app.get("/schools/{school_id}", response_model=SchoolResponse)
def read_school(school_id: int, db: Session = Depends(get_db)):
    school = db.query(schools).filter(schools.id == school_id).first()
    if school is None:
        raise HTTPException(status_code=404, detail="School not found")
    return school

@app.delete("/schools/{school_id}", response_model=SchoolResponse)
def delete_school(school_id: int, db: Session = Depends(get_db)):
    school = db.query(schools).filter(schools.id == school_id).first()
    if school is None:
        raise HTTPException(status_code=404, detail="School not found")
    db.delete(school)
    db.commit()
    return school

## for sessions table

@app.post("/sessions/", response_model=SessionResponse)
def create_session(session: SessionCreate, db: Session = Depends(get_db)):
    db_session = sessions(admin_id=session.admin_id, admin_email=session.admin_email, school_id=session.school_id, school=session.school, supervisor_id=session.supervisor_id, supervisor_email=session.supervisor_email, client_id=session.client_id, client_email=session.client_email, date=session.date)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

@app.get("/sessions/", response_model=List[SessionResponse])
def read_sessions(db: Session = Depends(get_db)):
    return db.query(sessions).all()

@app.get("/sessions/{session_id}", response_model=SessionResponse)
def read_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(sessions).filter(sessions.id == session_id).first()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@app.delete("/sessions/{session_id}", response_model=SessionResponse)
def delete_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(sessions).filter(sessions.id == session_id).first()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(session)
    db.commit()
    return session
