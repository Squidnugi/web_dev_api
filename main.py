from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import sessionmaker, Session, declarative_base, relationship
from pydantic import BaseModel
import os
from typing import List, Optional, Annotated
from datetime import date
import uvicorn


# Database Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./app.db"
)
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Needed for SQLite
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Table Models

class School(Base):
    __tablename__ = "schools"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    address = Column(String, index=True)
    city = Column(String, index=True)
    county = Column(String, index=True)
    postcode = Column(String, index=True)
    phone = Column(String, index=True)  # Note: Using String for phone number
    website = Column(String, index=True)
    domain = Column(String, unique=True, index=True)
    users = relationship("User", back_populates="school")
    sessions = relationship("Session", back_populates="school")
    session_edits = relationship("SessionEdit", back_populates="school")

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
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=True)  # Keep this column
    supervisor_id = Column(Integer, ForeignKey("users.id"))
    supervisor_email = Column(String)
    client_id = Column(Integer)
    client_email = Column(String)
    date = Column(String)
    request = Column(String)
    additional_info = Column(String)

    session = relationship("Session", back_populates="session_edits")
    user = relationship("User", back_populates="session_edits")
    school = relationship("School", back_populates="session_edits")  # Add this relationship

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
    session_id: Optional[int] = None
    school_id: Optional[int] = None
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

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
my_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c'

# Token Authentication
async def get_current_user(token: str = Depends(oauth2_scheme)):
    if token != my_token:
        raise HTTPException(status_code=400, detail="Unauthorized")
    return token

# Users Endpoints
@app.post("/users/", response_model=UserResponse)
async def create_user(token: Annotated[str, Depends(get_current_user)], user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/", response_model=List[UserResponse])
async def read_users(token: Annotated[str, Depends(get_current_user)], db: Session = Depends(get_db)):
    return db.query(User).all()

@app.get("/users/{user_id}", response_model=UserResponse)
async def read_user(token: Annotated[str, Depends(get_current_user)], user_id: str, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.put("/users/{user_id}", response_model=UserResponse)
async def update_user(token: Annotated[str, Depends(get_current_user)], user_id: str, user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    for key, value in user.dict().items():
        setattr(db_user, key, value)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.delete("/users/{user_id}")
async def delete_user(token: Annotated[str, Depends(get_current_user)], user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)
    db.commit()
    return {"message": "User deleted"}

# Schools Endpoints
@app.post("/schools/", response_model=SchoolResponse)
async def create_school(token: Annotated[str, Depends(get_current_user)], school: SchoolCreate, db: Session = Depends(get_db)):
    db_school = School(**school.dict())
    db.add(db_school)
    db.commit()
    db.refresh(db_school)
    return db_school

@app.get("/schools/", response_model=List[SchoolResponse])
async def read_schools(token: Annotated[str, Depends(get_current_user)], db: Session = Depends(get_db)):
    return db.query(School).all()

@app.get("/schools/{school_id}", response_model=SchoolResponse)
async def read_school(token: Annotated[str, Depends(get_current_user)], school_id: int, db: Session = Depends(get_db)):
    db_school = db.query(School).filter(School.id == school_id).first()
    if db_school is None:
        raise HTTPException(status_code=404, detail="School not found")
    return db_school

@app.put("/schools/{school_id}", response_model=SchoolResponse)
async def update_school(token: Annotated[str, Depends(get_current_user)], school_id: int, school: SchoolCreate, db: Session = Depends(get_db)):
    db_school = db.query(School).filter(School.id == school_id).first()
    if db_school is None:
        raise HTTPException(status_code=404, detail="School not found")
    for key, value in school.dict().items():
        setattr(db_school, key, value)
    db.commit()
    db.refresh(db_school)
    return db_school

@app.delete("/schools/{school_id}")
async def delete_school(token: Annotated[str, Depends(get_current_user)], school_id: int, db: Session = Depends(get_db)):
    db_school = db.query(School).filter(School.id == school_id).first()
    if db_school is None:
        raise HTTPException(status_code=404, detail="School not found")
    db.delete(db_school)
    db.commit()
    return {"message": "School deleted"}

# Sessions Endpoints
@app.post("/sessions/", response_model=SessionResponse)
async def create_session(token: Annotated[str, Depends(get_current_user)], session: SessionCreate, db: Session = Depends(get_db)):
    db_session = Session(**session.dict())
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

@app.get("/sessions/", response_model=List[SessionResponse])
async def read_sessions(token: Annotated[str, Depends(get_current_user)], db: Session = Depends(get_db)):
    return db.query(Session).all()

@app.get("/sessions/{session_id}", response_model=SessionResponse)
async def read_session(token: Annotated[str, Depends(get_current_user)], session_id: int, db: Session = Depends(get_db)):
    db_session = db.query(Session).filter(Session.id == session_id).first()
    if db_session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return db_session

@app.put("/sessions/{session_id}", response_model=SessionResponse)
async def update_session(token: Annotated[str, Depends(get_current_user)], session_id: int, session: SessionCreate, db: Session = Depends(get_db)):
    db_session = db.query(Session).filter(Session.id == session_id).first()
    if db_session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    for key, value in session.dict().items():
        setattr(db_session, key, value)
    db.commit()
    db.refresh(db_session)
    return db_session

@app.delete("/sessions/{session_id}")
async def delete_session(token: Annotated[str, Depends(get_current_user)], session_id: int, db: Session = Depends(get_db)):
    db_session = db.query(Session).filter(Session.id == session_id).first()
    if db_session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(db_session)
    db.commit()
    return {"message": "Session deleted"}


@app.get("/sessions/{supervisor_id}", response_model=List[SessionResponse])
async def read_sessions_by_supervisor(token: Annotated[str, Depends(get_current_user)], supervisor_id: str, db: Session = Depends(get_db)):
    return db.query(Session).filter(Session.supervisor_email == supervisor_id).all()

@app.get("/sessions/{client_id}", response_model=List[SessionResponse])
async def read_sessions_by_client(token: Annotated[str, Depends(get_current_user)], client_id: str, db: Session = Depends(get_db)):
    return db.query(Session).filter(Session.client_email == client_id).all()

@app.get("/sessions/{school_id}/", response_model=List[SessionResponse])
async def read_sessions_by_school(token: Annotated[str, Depends(get_current_user)], school_id: int, db: Session = Depends(get_db)):
    return db.query(Session).filter(Session.school_id == school_id).all()

# Contacts Endpoints
@app.post("/contact/", response_model=ContactResponse)
async def create_contact(token: Annotated[str, Depends(get_current_user)], contact: ContactCreate, db: Session = Depends(get_db)):
    db_contact = Contact(**contact.dict())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

@app.get("/contact/", response_model=List[ContactResponse])
async def read_contacts(token: Annotated[str, Depends(get_current_user)], db: Session = Depends(get_db)):
    return db.query(Contact).all()

@app.get("/contact/{contact_id}", response_model=ContactResponse)
async def read_contact(token: Annotated[str, Depends(get_current_user)], contact_id: int, db: Session = Depends(get_db)):
    db_contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact

@app.delete("/contact/{contact_id}")
async def delete_contact(token: Annotated[str, Depends(get_current_user)], contact_id: int, db: Session = Depends(get_db)):
    db_contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    db.delete(db_contact)
    db.commit()
    return {"message": "Contact deleted"}

# Session_edit endpoints
@app.post("/session_edits/", response_model=SessionEditResponse)
async def create_session_edit(token: Annotated[str, Depends(get_current_user)], session_edit: SessionEditCreate, db: Session = Depends(get_db)):
    db_session_edit = SessionEdit(**session_edit.dict())
    db.add(db_session_edit)
    db.commit()
    db.refresh(db_session_edit)
    return db_session_edit

@app.get("/session_edits/", response_model=List[SessionEditResponse])
async def read_session_edits(token: Annotated[str, Depends(get_current_user)], db: Session = Depends(get_db)):
    session_edits = db.query(SessionEdit).all()
    if not session_edits:
        raise HTTPException(status_code=404, detail="Session Edit not found")
    return session_edits

@app.get("/session_edits/{session_edit_id}", response_model=SessionEditResponse)
async def read_session_edit(token: Annotated[str, Depends(get_current_user)], session_edit_id: int, db: Session = Depends(get_db)):
    db_session_edit = db.query(SessionEdit).filter(SessionEdit.id == session_edit_id).first()
    if db_session_edit is None:
        raise HTTPException(status_code=404, detail="Session Edit not found")
    return db_session_edit

@app.delete("/session_edits/{session_edit_id}")
async def delete_session_edit(token: Annotated[str, Depends(get_current_user)], session_edit_id: int, db: Session = Depends(get_db)):
    db_session_edit = db.query(SessionEdit).filter(SessionEdit.id == session_edit_id).first()
    if db_session_edit is None:
        raise HTTPException(status_code=404, detail="Session Edit not found")
    db.delete(db_session_edit)
    db.commit()
    return {"message": "Session Edit deleted"}

@app.get("/session_edits/supervisor/{supervisor_id}", response_model=List[SessionEditResponse])
async def read_session_edits_by_supervisor(token: Annotated[str, Depends(get_current_user)], supervisor_id: str, db: Session = Depends(get_db)):
    session_edits = db.query(SessionEdit).filter(SessionEdit.supervisor_email == supervisor_id).all()
    if not session_edits:
        raise HTTPException(status_code=404, detail="Session Edit not found")
    return session_edits

@app.get("/session_edits/client/{client_id}", response_model=List[SessionEditResponse])
async def read_session_edits_by_client(token: Annotated[str, Depends(get_current_user)], client_id: str, db: Session = Depends(get_db)):
    session_edits = db.query(SessionEdit).filter(SessionEdit.client_email == client_id).all()
    if not session_edits:
        raise HTTPException(status_code=404, detail="Session Edit not found")
    return session_edits

@app.get("/session_edits/school/{school_id}", response_model=List[SessionEditResponse])
async def read_session_edits_by_school(token: Annotated[str, Depends(get_current_user)], school_id: int, db: Session = Depends(get_db)):
    session_edits = db.query(SessionEdit).join(Session).filter(Session.school_id == school_id).all()
    if not session_edits:
        raise HTTPException(status_code=404, detail="Session Edit not found")
    return session_edits

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)