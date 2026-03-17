from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from passlib.context import CryptContext
from fastapi.staticfiles import StaticFiles # Add this
from sqlalchemy import Float # Add Float for the price

# --- 1. Database Setup (MySQL) ---
# Update YOUR_PASSWORD_HERE to your actual MySQL root password
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 2. Database Model ---
# --- 2. Database Model ---
class DBUser(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

# This needs to be its own separate class!
class DBItem(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    price = Column(Float, nullable=False)
    image_filename = Column(String(255), nullable=False)
    # --- New Detailed Columns ---
    model = Column(String(255), nullable=False)
    year = Column(Integer, nullable=False)
    vehicle_type = Column(String(50), nullable=False) # e.g., Motorbike, Scooter
    cc = Column(Integer, nullable=False)
    mileage = Column(String(50), nullable=False)
    is_available = Column(Integer, default=1)

Base.metadata.create_all(bind=engine)

# --- 3. Pydantic Schemas ---
class UserCreate(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

# --- 4. Security & Hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 5. App & CORS ---
app = FastAPI()

# Tell FastAPI to serve the 'static' folder we just created
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

# --- 6. Endpoints ---
@app.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(DBUser).filter(DBUser.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pwd = get_password_hash(user.password)
    new_user = DBUser(email=user.email, hashed_password=hashed_pwd)
    
    db.add(new_user)
    db.commit()
    
    return {"message": "User created successfully"}

@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(DBUser).filter(DBUser.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
    return {"message": "Login successful"}
class ItemResponse(BaseModel):
    id: int
    name: str
    price: float
    image_filename: str
    model: str
    year: int
    vehicle_type: str
    cc: int
    mileage: str
    is_available: int

    class Config:
        from_attributes = True
@app.get("/items", response_model=list[ItemResponse])
def get_items(db: Session = Depends(get_db)):
    items = db.query(DBItem).all()
    return items
