from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import sessionmaker, Session, declarative_base, relationship
from pydantic import BaseModel
import os
from typing import List, Optional
from datetime import date
import uvicorn

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Models

class School(Base):
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
    users = relationship("User", back_populates="school")
    sessions = relationship("Session", back_populates="school")

class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"))
    supervisor_id = Column(Integer, ForeignKey("users.id"), index=True)
    supervisor_email = Column(String, index=True)
    client_id = Column(Integer, ForeignKey("users.id"), index=True)
    client_email = Column(String, index=True)
    date = Column(Date, index=True)
    additional_info = Column(String, nullable=True)
    supervisor = relationship("User", foreign_keys=[supervisor_id], back_populates="supervised_sessions")
    client = relationship("User", foreign_keys=[client_id], back_populates="client_sessions")
    session_edits = relationship("SessionEdit", back_populates="session")
    school = relationship("School", back_populates="sessions")

class SessionEdit(Base):
    __tablename__ = "session_edits"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    supervisor_id = Column(Integer, ForeignKey("users.id"))
    supervisor_email = Column(String)
    client_id = Column(Integer)
    client_email = Column(String)
    date = Column(Date)
    request = Column(String)
    additional_info = Column(String, nullable=True)
    session = relationship("Session", back_populates="session_edits")
    user = relationship("User", back_populates="session_edits")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    account_type = Column(String)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=True)
    supervised_sessions = relationship("Session", foreign_keys="[Session.supervisor_id]", back_populates="supervisor")
    client_sessions = relationship("Session", foreign_keys="[Session.client_id]", back_populates="client")
    session_edits = relationship("SessionEdit", back_populates="user")
    school = relationship("School", back_populates="users")


class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, index=True)
    message = Column(String)

# Create Tables
Base.metadata.create_all(bind=engine)

# Pydantic Models
class UserCreate(BaseModel):
    email: str
    password: str
    account_type: str
    school_id: Optional[int] = None

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
    school_id: Optional[int] = None
    supervisor_id: int
    supervisor_email: str
    client_id: int
    client_email: str
    date: date
    additional_info: Optional[str] = None

class SessionEditCreate(BaseModel):
    session_id: int
    supervisor_id: int
    supervisor_email: str
    client_id: int
    client_email: str
    date: date
    request: str
    additional_info: Optional[str] = None

class ContactCreate(BaseModel):
    name: str
    email: str
    message: str

# Response Models
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

class SessionEditResponse(SessionEditCreate):
    id: int
    class Config:
        from_attributes = True

class ContactResponse(ContactCreate):
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

# Users Endpoints
@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/", response_model=List[UserResponse])
def read_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@app.get("/users/{user_id}", response_model=UserResponse)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    for key, value in user.dict().items():
        setattr(db_user, key, value)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)
    db.commit()
    return {"message": "User deleted"}

# Schools Endpoints
@app.post("/schools/", response_model=SchoolResponse)
def create_school(school: SchoolCreate, db: Session = Depends(get_db)):
    db_school = School(**school.dict())
    db.add(db_school)
    db.commit()
    db.refresh(db_school)
    return db_school

@app.get("/schools/", response_model=List[SchoolResponse])
def read_schools(db: Session = Depends(get_db)):
    return db.query(School).all()

@app.get("/schools/{school_id}", response_model=SchoolResponse)
def read_school(school_id: int, db: Session = Depends(get_db)):
    db_school = db.query(School).filter(School.id == school_id).first()
    if db_school is None:
        raise HTTPException(status_code=404, detail="School not found")
    return db_school

@app.put("/schools/{school_id}", response_model=SchoolResponse)
def update_school(school_id: int, school: SchoolCreate, db: Session = Depends(get_db)):
    db_school = db.query(School).filter(School.id == school_id).first()
    if db_school is None:
        raise HTTPException(status_code=404, detail="School not found")
    for key, value in school.dict().items():
        setattr(db_school, key, value)
    db.commit()
    db.refresh(db_school)
    return db_school

@app.delete("/schools/{school_id}")
def delete_school(school_id: int, db: Session = Depends(get_db)):
    db_school = db.query(School).filter(School.id == school_id).first()
    if db_school is None:
        raise HTTPException(status_code=404, detail="School not found")
    db.delete(db_school)
    db.commit()
    return {"message": "School deleted"}

# Sessions Endpoints
@app.post("/sessions/", response_model=SessionResponse)
def create_session(session: SessionCreate, db: Session = Depends(get_db)):
    db_session = Session(**session.dict())
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

@app.get("/sessions/", response_model=List[SessionResponse])
def read_sessions(db: Session = Depends(get_db)):
    return db.query(Session).all()

@app.get("/sessions/{session_id}", response_model=SessionResponse)
def read_session(session_id: int, db: Session = Depends(get_db)):
    db_session = db.query(Session).filter(Session.id == session_id).first()
    if db_session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return db_session

@app.put("/sessions/{session_id}", response_model=SessionResponse)
def update_session(session_id: int, session: SessionCreate, db: Session = Depends(get_db)):
    db_session = db.query(Session).filter(Session.id == session_id).first()
    if db_session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    for key, value in session.dict().items():
        setattr(db_session, key, value)
    db.commit()
    db.refresh(db_session)
    return db_session

@app.delete("/sessions/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db)):
    db_session = db.query(Session).filter(Session.id == session_id).first()
    if db_session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(db_session)
    db.commit()
    return {"message": "Session deleted"}

# Contacts Endpoints
@app.post("/contact/", response_model=ContactResponse)
def create_contact(contact: ContactCreate, db: Session = Depends(get_db)):
    db_contact = Contact(**contact.dict())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

@app.get("/contact/", response_model=List[ContactResponse])
def read_contacts(db: Session = Depends(get_db)):
    return db.query(Contact).all()

@app.get("/contact/{contact_id}", response_model=ContactResponse)
def read_contact(contact_id: int, db: Session = Depends(get_db)):
    db_contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact

@app.delete("/contact/{contact_id}")
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    db_contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    db.delete(db_contact)
    db.commit()
    return {"message": "Contact deleted"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
