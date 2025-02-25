from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, Session, declarative_base
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
    password = Column(String,index=True)
    account_type = Column(String, index=True)

class schools(Base):
    __tablename__ = "schools"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    address = Column(String, index=True)
    city = Column(String, index=True)
    state = Column(String, index=True)
    zip = Column(String, index=True)
    phone = Column(String, index=True)
    email = Column(String, index=True)
    website = Column(String, index=True)
    domain = Column(String, index=True)

class sessions(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey('users.id'), index=True)
    admin_email = Column(String, index=True)
    school_id = Column(Integer, ForeignKey('schools.id'), index=True)
    school = Column(String, index=True)
    supervisor_id = Column(Integer, ForeignKey('users.id'), index=True)
    supervisor_email = Column(String, index=True)
    client_id = Column(Integer, ForeignKey('users.id'), index=True)
    client_email = Column(String, index=True)
    date = Column(Date, index=True)

# Create Tables
Base.metadata.create_all(bind=engine)

# Pydantic Schema
class UserCreate(BaseModel):
    email: str
    password: str
    account_type: str

class UserResponse(UserCreate):
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

## for sessions table