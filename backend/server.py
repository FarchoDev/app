from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timedelta, timezone
import jwt
from passlib.context import CryptContext
import bcrypt

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-here-please-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Create the main app without a prefix
app = FastAPI(title="ISTQB Study Platform API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# User Models
class UserBase(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    full_name: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    study_progress: dict = Field(default_factory=dict)
    total_score: int = 0
    modules_completed: int = 0

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    is_active: bool
    created_at: datetime
    study_progress: dict
    total_score: int
    modules_completed: int

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# ISTQB Module Models
class ISTQBModuleSection(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    order: int

class ISTQBModule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    content: str
    sections: List[ISTQBModuleSection] = Field(default_factory=list)
    order: int
    estimated_time: int  # in minutes
    learning_objectives: List[str] = Field(default_factory=list)
    key_concepts: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ISTQBModuleCreate(BaseModel):
    title: str
    description: str
    content: str
    sections: List[ISTQBModuleSection] = Field(default_factory=list)
    order: int
    estimated_time: int
    learning_objectives: List[str] = Field(default_factory=list)
    key_concepts: List[str] = Field(default_factory=list)

class UserProgress(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    module_id: str
    completed: bool = False
    progress_percentage: int = 0
    time_spent: int = 0  # in minutes
    sections_completed: List[str] = Field(default_factory=list)  # List of section IDs
    last_accessed: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_section_accessed: Optional[str] = None

# Auth Functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"email": email})
    if user is None:
        raise credentials_exception
    return UserResponse(**user)

# Auth Routes
@api_router.post("/auth/register", response_model=Token)
async def register(user: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    user_dict = user.dict()
    user_dict.pop('password')
    
    new_user = UserBase(**user_dict)
    user_data = new_user.dict()
    user_data['hashed_password'] = hashed_password
    
    await db.users.insert_one(user_data)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    user_response = UserResponse(**new_user.dict())
    return {"access_token": access_token, "token_type": "bearer", "user": user_response}

@api_router.post("/auth/login", response_model=Token)
async def login(user_credentials: UserLogin):
    user = await db.users.find_one({"email": user_credentials.email})
    if not user or not verify_password(user_credentials.password, user['hashed_password']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user['email']}, expires_delta=access_token_expires
    )
    
    user_response = UserResponse(**user)
    return {"access_token": access_token, "token_type": "bearer", "user": user_response}

@api_router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserResponse = Depends(get_current_user)):
    return current_user

# ISTQB Module Routes
@api_router.get("/modules", response_model=List[ISTQBModule])
async def get_modules():
    modules = await db.istqb_modules.find().sort("order", 1).to_list(1000)
    return [ISTQBModule(**module) for module in modules]

@api_router.get("/modules/{module_id}", response_model=ISTQBModule)
async def get_module(module_id: str):
    module = await db.istqb_modules.find_one({"id": module_id})
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    return ISTQBModule(**module)

@api_router.post("/modules", response_model=ISTQBModule)
async def create_module(module: ISTQBModuleCreate, current_user: UserResponse = Depends(get_current_user)):
    new_module = ISTQBModule(**module.dict())
    await db.istqb_modules.insert_one(new_module.dict())
    return new_module

# User Progress Routes
@api_router.get("/progress", response_model=List[UserProgress])
async def get_user_progress(current_user: UserResponse = Depends(get_current_user)):
    progress = await db.user_progress.find({"user_id": current_user.id}).to_list(1000)
    return [UserProgress(**p) for p in progress]

@api_router.post("/progress/{module_id}")
async def update_progress(
    module_id: str, 
    progress_percentage: int, 
    time_spent: int,
    section_id: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    # Get existing progress
    existing_progress = await db.user_progress.find_one({
        "user_id": current_user.id,
        "module_id": module_id
    })
    
    sections_completed = existing_progress.get('sections_completed', []) if existing_progress else []
    
    # Add section to completed if provided and not already there
    if section_id and section_id not in sections_completed:
        sections_completed.append(section_id)
    
    # Update progress data
    progress_data = {
        "user_id": current_user.id,
        "module_id": module_id,
        "progress_percentage": progress_percentage,
        "time_spent": time_spent,
        "completed": progress_percentage >= 100,
        "sections_completed": sections_completed,
        "last_accessed": datetime.now(timezone.utc),
        "last_section_accessed": section_id
    }
    
    if existing_progress:
        await db.user_progress.update_one(
            {"user_id": current_user.id, "module_id": module_id},
            {"$set": progress_data}
        )
    else:
        new_progress = UserProgress(**progress_data)
        await db.user_progress.insert_one(new_progress.dict())
    
    return {"message": "Progress updated successfully"}

@api_router.post("/progress/{module_id}/section/{section_id}")
async def mark_section_complete(
    module_id: str,
    section_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Mark a specific section as completed"""
    existing_progress = await db.user_progress.find_one({
        "user_id": current_user.id,
        "module_id": module_id
    })
    
    sections_completed = existing_progress.get('sections_completed', []) if existing_progress else []
    
    if section_id not in sections_completed:
        sections_completed.append(section_id)
    
    # Get module to calculate progress percentage
    module = await db.istqb_modules.find_one({"id": module_id})
    if module:
        total_sections = len(module.get('sections', []))
        progress_percentage = round((len(sections_completed) / total_sections * 100)) if total_sections > 0 else 100
    else:
        progress_percentage = 100
    
    progress_data = {
        "user_id": current_user.id,
        "module_id": module_id,
        "sections_completed": sections_completed,
        "progress_percentage": progress_percentage,
        "completed": progress_percentage >= 100,
        "last_accessed": datetime.now(timezone.utc),
        "last_section_accessed": section_id
    }
    
    if existing_progress:
        # Update existing progress
        await db.user_progress.update_one(
            {"user_id": current_user.id, "module_id": module_id},
            {"$set": progress_data}
        )
    else:
        # Create new progress
        progress_data["time_spent"] = 0
        progress_data["id"] = str(uuid.uuid4())
        await db.user_progress.insert_one(progress_data)
    
    return {
        "message": "Section marked as complete",
        "progress_percentage": progress_percentage,
        "sections_completed": len(sections_completed)
    }

# Dashboard Stats
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: UserResponse = Depends(get_current_user)):
    total_modules = await db.istqb_modules.count_documents({})
    user_progress = await db.user_progress.find({"user_id": current_user.id}).to_list(1000)
    
    completed_modules = len([p for p in user_progress if p.get('completed', False)])
    total_time_spent = sum([p.get('time_spent', 0) for p in user_progress])
    
    return {
        "total_modules": total_modules,
        "completed_modules": completed_modules,
        "total_time_spent": total_time_spent,
        "completion_percentage": round((completed_modules / total_modules * 100) if total_modules > 0 else 0, 1)
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    # Create sample ISTQB modules if they don't exist
    existing_modules = await db.istqb_modules.count_documents({})
    if existing_modules == 0:
        sample_modules = [
            {
                "id": str(uuid.uuid4()),
                "title": "1. Fundamentos de las Pruebas",
                "description": "Introducción a los conceptos básicos de testing, terminología y principios fundamentales.",
                "content": "En este módulo aprenderás los 7 principios fundamentales del testing, la diferencia entre errores, defectos y fallos, y la importancia del testing en el desarrollo de software.",
                "order": 1,
                "estimated_time": 45,
                "created_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "title": "2. Testing a lo largo del Ciclo de Vida del Software",
                "description": "Cómo se integra el testing en diferentes modelos de ciclo de vida del desarrollo.",
                "content": "Exploraremos cómo el testing se adapta a metodologías como Waterfall, Agile, y DevOps, y cómo las actividades de testing varían en cada fase.",
                "order": 2,
                "estimated_time": 50,
                "created_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "title": "3. Técnicas de Testing Estático",
                "description": "Revisiones, walkthroughs, inspecciones y análisis estático de código.",
                "content": "Aprende sobre las técnicas de testing que no requieren ejecutar el código, incluyendo revisiones formales e informales.",
                "order": 3,
                "estimated_time": 40,
                "created_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "title": "4. Técnicas de Diseño de Pruebas",
                "description": "Técnicas de caja negra, caja blanca y basadas en la experiencia.",
                "content": "Domina las técnicas para diseñar casos de prueba efectivos, incluyendo partición de equivalencia, análisis de valores límite y más.",
                "order": 4,
                "estimated_time": 60,
                "created_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "title": "5. Gestión de las Pruebas",
                "description": "Planificación, estimación, monitoreo y control de las actividades de testing.",
                "content": "Aprende a crear planes de prueba, estimar esfuerzo, gestionar riesgos y reportar el progreso del testing.",
                "order": 5,
                "estimated_time": 55,
                "created_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "title": "6. Herramientas para el Testing",
                "description": "Clasificación y uso de herramientas de apoyo al testing.",
                "content": "Conoce las diferentes categorías de herramientas de testing y cómo pueden mejorar la eficiencia y efectividad de tus pruebas.",
                "order": 6,
                "estimated_time": 35,
                "created_at": datetime.now(timezone.utc)
            }
        ]
        
        await db.istqb_modules.insert_many(sample_modules)
        logger.info("Sample ISTQB modules created")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()