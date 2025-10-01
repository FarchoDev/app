from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
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
import aiofiles
import shutil

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Create uploads directory
UPLOAD_DIR = ROOT_DIR / 'uploads'
UPLOAD_DIR.mkdir(exist_ok=True)

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

# Document Management Models
class DocumentCategory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    color: str = "#3B82F6"  # Default blue color
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DocumentCategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    color: str = "#3B82F6"

class Document(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    original_filename: str
    title: str
    description: Optional[str] = None
    file_size: int  # in bytes
    file_path: str
    mime_type: str = "application/pdf"
    category_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    uploaded_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed: Optional[datetime] = None
    download_count: int = 0
    is_public: bool = False

class DocumentCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    is_public: bool = False

class DocumentResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    title: str
    description: Optional[str]
    file_size: int
    mime_type: str
    category_id: Optional[str]
    category_name: Optional[str] = None
    tags: List[str]
    uploaded_by: str
    created_at: datetime
    last_accessed: Optional[datetime]
    download_count: int
    is_public: bool

# Quiz Models
class QuestionOption(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    is_correct: bool
    explanation: Optional[str] = None

class Question(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    module_id: str
    section_id: Optional[str] = None
    question_text: str
    question_type: str = "multiple_choice"  # multiple_choice, true_false
    options: List[QuestionOption]
    difficulty: str = "medium"  # easy, medium, hard
    topic: str  # topic/theme within the module
    explanation: str  # General explanation of the concept
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class QuestionCreate(BaseModel):
    module_id: str
    section_id: Optional[str] = None
    question_text: str
    question_type: str = "multiple_choice"
    options: List[QuestionOption]
    difficulty: str = "medium"
    topic: str
    explanation: str

class Quiz(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    module_id: Optional[str] = None  # None for general/mixed quizzes
    quiz_type: str  # "practice", "module_test", "final_exam"
    question_ids: List[str]
    time_limit: Optional[int] = None  # in minutes, None for no limit
    passing_score: int = 70  # percentage
    randomize_questions: bool = True
    randomize_options: bool = True
    show_results_immediately: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class QuizCreate(BaseModel):
    title: str
    description: str
    module_id: Optional[str] = None
    quiz_type: str
    question_ids: List[str]
    time_limit: Optional[int] = None
    passing_score: int = 70
    randomize_questions: bool = True
    randomize_options: bool = True
    show_results_immediately: bool = True

class QuizAttempt(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    quiz_id: str
    answers: dict  # {question_id: selected_option_id}
    score: Optional[int] = None  # percentage
    passed: Optional[bool] = None
    time_taken: Optional[int] = None  # in seconds
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    is_completed: bool = False

class QuizAnswer(BaseModel):
    question_id: str
    selected_option_id: str

class QuizSubmission(BaseModel):
    quiz_id: str
    answers: List[QuizAnswer]
    time_taken: Optional[int] = None  # in seconds

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
    quiz_attempts = await db.quiz_attempts.find({"user_id": current_user.id, "is_completed": True}).to_list(1000)
    
    completed_modules = len([p for p in user_progress if p.get('completed', False)])
    total_time_spent = sum([p.get('time_spent', 0) for p in user_progress])
    
    # Get document stats
    total_documents = await db.documents.count_documents({"uploaded_by": current_user.id})
    
    # Quiz statistics
    total_quizzes_taken = len(quiz_attempts)
    average_score = round(sum([attempt.get('score', 0) for attempt in quiz_attempts]) / total_quizzes_taken) if total_quizzes_taken > 0 else 0
    
    return {
        "total_modules": total_modules,
        "completed_modules": completed_modules,
        "total_time_spent": total_time_spent,
        "total_documents": total_documents,
        "completion_percentage": round((completed_modules / total_modules * 100) if total_modules > 0 else 0, 1),
        "total_quizzes_taken": total_quizzes_taken,
        "average_quiz_score": average_score
    }

# Document Category Routes
@api_router.get("/categories", response_model=List[DocumentCategory])
async def get_categories(current_user: UserResponse = Depends(get_current_user)):
    categories = await db.document_categories.find({"created_by": current_user.id}).to_list(1000)
    return [DocumentCategory(**cat) for cat in categories]

@api_router.post("/categories", response_model=DocumentCategory)
async def create_category(
    category: DocumentCategoryCreate, 
    current_user: UserResponse = Depends(get_current_user)
):
    new_category = DocumentCategory(**category.dict(), created_by=current_user.id)
    await db.document_categories.insert_one(new_category.dict())
    return new_category

@api_router.put("/categories/{category_id}", response_model=DocumentCategory)
async def update_category(
    category_id: str,
    category: DocumentCategoryCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    existing_category = await db.document_categories.find_one({
        "id": category_id,
        "created_by": current_user.id
    })
    
    if not existing_category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    updated_data = category.dict()
    await db.document_categories.update_one(
        {"id": category_id},
        {"$set": updated_data}
    )
    
    updated_category = DocumentCategory(**{**existing_category, **updated_data})
    return updated_category

@api_router.delete("/categories/{category_id}")
async def delete_category(
    category_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    category = await db.document_categories.find_one({
        "id": category_id,
        "created_by": current_user.id
    })
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Check if category has documents
    documents_count = await db.documents.count_documents({"category_id": category_id})
    if documents_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete category with {documents_count} documents. Move or delete documents first."
        )
    
    await db.document_categories.delete_one({"id": category_id})
    return {"message": "Category deleted successfully"}

# Document Management Routes
@api_router.get("/documents", response_model=List[DocumentResponse])
async def get_documents(
    category_id: Optional[str] = None,
    search: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    # Build query
    query = {"uploaded_by": current_user.id}
    if category_id:
        query["category_id"] = category_id
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"tags": {"$regex": search, "$options": "i"}}
        ]
    
    documents = await db.documents.find(query).sort("created_at", -1).to_list(1000)
    
    # Enrich with category names
    result = []
    for doc in documents:
        doc_response = DocumentResponse(**doc)
        if doc.get("category_id"):
            category = await db.document_categories.find_one({"id": doc["category_id"]})
            if category:
                doc_response.category_name = category["name"]
        result.append(doc_response)
    
    return result

@api_router.post("/documents/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    category_id: Optional[str] = Form(None),
    tags: str = Form(""),  # Comma-separated tags
    is_public: bool = Form(False),
    current_user: UserResponse = Depends(get_current_user)
):
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Create unique filename
    file_id = str(uuid.uuid4())
    file_extension = ".pdf"
    unique_filename = f"{file_id}{file_extension}"
    
    # Save file
    file_path = UPLOAD_DIR / unique_filename
    
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Parse tags
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else []
        
        # Create document record
        document_data = {
            "id": str(uuid.uuid4()),
            "filename": unique_filename,
            "original_filename": file.filename,
            "title": title,
            "description": description,
            "file_size": len(content),
            "file_path": str(file_path),
            "mime_type": file.content_type or "application/pdf",
            "category_id": category_id,
            "tags": tag_list,
            "uploaded_by": current_user.id,
            "created_at": datetime.now(timezone.utc),
            "download_count": 0,
            "is_public": is_public
        }
        
        # Validate category exists if provided
        if category_id:
            category = await db.document_categories.find_one({
                "id": category_id,
                "created_by": current_user.id
            })
            if not category:
                # Clean up uploaded file
                if file_path.exists():
                    file_path.unlink()
                raise HTTPException(status_code=400, detail="Invalid category")
        
        await db.documents.insert_one(document_data)
        
        # Create response
        doc_response = DocumentResponse(**document_data)
        if category_id:
            category = await db.document_categories.find_one({"id": category_id})
            if category:
                doc_response.category_name = category["name"]
        
        return doc_response
    
    except Exception as e:
        # Clean up file if error occurred
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@api_router.get("/documents/{document_id}")
async def download_document(
    document_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    document = await db.documents.find_one({
        "id": document_id,
        "$or": [
            {"uploaded_by": current_user.id},
            {"is_public": True}
        ]
    })
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    file_path = Path(document["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    # Update download count and last accessed
    await db.documents.update_one(
        {"id": document_id},
        {
            "$inc": {"download_count": 1},
            "$set": {"last_accessed": datetime.now(timezone.utc)}
        }
    )
    
    return FileResponse(
        path=file_path,
        filename=document["original_filename"],
        media_type=document["mime_type"]
    )

@api_router.put("/documents/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: str,
    title: str = Form(...),
    description: Optional[str] = Form(None),
    category_id: Optional[str] = Form(None),
    tags: str = Form(""),
    is_public: bool = Form(False),
    current_user: UserResponse = Depends(get_current_user)
):
    document = await db.documents.find_one({
        "id": document_id,
        "uploaded_by": current_user.id
    })
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Validate category if provided
    if category_id:
        category = await db.document_categories.find_one({
            "id": category_id,
            "created_by": current_user.id
        })
        if not category:
            raise HTTPException(status_code=400, detail="Invalid category")
    
    # Parse tags
    tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else []
    
    # Update document
    update_data = {
        "title": title,
        "description": description,
        "category_id": category_id,
        "tags": tag_list,
        "is_public": is_public
    }
    
    await db.documents.update_one(
        {"id": document_id},
        {"$set": update_data}
    )
    
    # Get updated document
    updated_doc = await db.documents.find_one({"id": document_id})
    doc_response = DocumentResponse(**updated_doc)
    
    if category_id:
        category = await db.document_categories.find_one({"id": category_id})
        if category:
            doc_response.category_name = category["name"]
    
    return doc_response

@api_router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    document = await db.documents.find_one({
        "id": document_id,
        "uploaded_by": current_user.id
    })
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete file from disk
    file_path = Path(document["file_path"])
    if file_path.exists():
        file_path.unlink()
    
    # Delete from database
    await db.documents.delete_one({"id": document_id})
    
    return {"message": "Document deleted successfully"}

# Quiz Routes
@api_router.get("/questions", response_model=List[Question])
async def get_questions(module_id: Optional[str] = None, difficulty: Optional[str] = None):
    """Get questions, optionally filtered by module and difficulty"""
    filter_dict = {}
    if module_id:
        filter_dict["module_id"] = module_id
    if difficulty:
        filter_dict["difficulty"] = difficulty
    
    questions = await db.questions.find(filter_dict).to_list(1000)
    return [Question(**question) for question in questions]

@api_router.get("/questions/{question_id}", response_model=Question)
async def get_question(question_id: str):
    """Get a specific question by ID"""
    question = await db.questions.find_one({"id": question_id})
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return Question(**question)

@api_router.post("/questions", response_model=Question)
async def create_question(question: QuestionCreate, current_user: UserResponse = Depends(get_current_user)):
    """Create a new question"""
    new_question = Question(**question.dict())
    await db.questions.insert_one(new_question.dict())
    return new_question

@api_router.get("/quizzes", response_model=List[Quiz])
async def get_quizzes(module_id: Optional[str] = None, quiz_type: Optional[str] = None):
    """Get quizzes, optionally filtered by module and type"""
    filter_dict = {}
    if module_id:
        filter_dict["module_id"] = module_id
    if quiz_type:
        filter_dict["quiz_type"] = quiz_type
    
    quizzes = await db.quizzes.find(filter_dict).to_list(1000)
    return [Quiz(**quiz) for quiz in quizzes]

@api_router.get("/quizzes/{quiz_id}", response_model=Quiz)
async def get_quiz(quiz_id: str):
    """Get a specific quiz by ID"""
    quiz = await db.quizzes.find_one({"id": quiz_id})
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return Quiz(**quiz)

@api_router.post("/quizzes", response_model=Quiz)
async def create_quiz(quiz: QuizCreate, current_user: UserResponse = Depends(get_current_user)):
    """Create a new quiz"""
    new_quiz = Quiz(**quiz.dict())
    await db.quizzes.insert_one(new_quiz.dict())
    return new_quiz

@api_router.get("/quizzes/{quiz_id}/questions")
async def get_quiz_questions(quiz_id: str, randomize: bool = True):
    """Get questions for a specific quiz"""
    quiz = await db.quizzes.find_one({"id": quiz_id})
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Get questions
    questions = []
    for question_id in quiz.get("question_ids", []):
        question = await db.questions.find_one({"id": question_id})
        if question:
            # Remove correct answers from options for the frontend
            question_data = Question(**question).dict()
            for option in question_data["options"]:
                option.pop("is_correct", None)  # Remove correct answer info
            questions.append(question_data)
    
    # Randomize questions if requested
    if randomize and quiz.get("randomize_questions", True):
        import random
        random.shuffle(questions)
    
    # Randomize options within each question if requested
    if quiz.get("randomize_options", True):
        import random
        for question in questions:
            random.shuffle(question["options"])
    
    return {
        "quiz": Quiz(**quiz).dict(),
        "questions": questions
    }

@api_router.post("/quizzes/{quiz_id}/attempt")
async def start_quiz_attempt(quiz_id: str, current_user: UserResponse = Depends(get_current_user)):
    """Start a new quiz attempt"""
    quiz = await db.quizzes.find_one({"id": quiz_id})
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    attempt = QuizAttempt(
        user_id=current_user.id,
        quiz_id=quiz_id,
        answers={}
    )
    
    await db.quiz_attempts.insert_one(attempt.dict())
    return {"attempt_id": attempt.id, "started_at": attempt.started_at}

@api_router.post("/quizzes/{quiz_id}/submit")
async def submit_quiz(quiz_id: str, submission: QuizSubmission, current_user: UserResponse = Depends(get_current_user)):
    """Submit quiz answers and get results"""
    # Find the most recent incomplete attempt
    attempt = await db.quiz_attempts.find_one({
        "user_id": current_user.id,
        "quiz_id": quiz_id,
        "is_completed": False
    })
    
    if not attempt:
        raise HTTPException(status_code=404, detail="No active quiz attempt found")
    
    # Get quiz and questions
    quiz = await db.quizzes.find_one({"id": quiz_id})
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Calculate score
    total_questions = len(quiz.get("question_ids", []))
    correct_answers = 0
    detailed_results = []
    
    # Convert answers to dict for easier access
    answers_dict = {answer.question_id: answer.selected_option_id for answer in submission.answers}
    
    for question_id in quiz.get("question_ids", []):
        question = await db.questions.find_one({"id": question_id})
        if question:
            selected_option_id = answers_dict.get(question_id)
            correct_option = next((opt for opt in question["options"] if opt["is_correct"]), None)
            is_correct = selected_option_id == correct_option["id"] if correct_option else False
            
            if is_correct:
                correct_answers += 1
            
            detailed_results.append({
                "question_id": question_id,
                "question_text": question["question_text"],
                "selected_option_id": selected_option_id,
                "correct_option_id": correct_option["id"] if correct_option else None,
                "is_correct": is_correct,
                "options": question["options"],
                "explanation": question.get("explanation", "")
            })
    
    score = round((correct_answers / total_questions * 100)) if total_questions > 0 else 0
    passed = score >= quiz.get("passing_score", 70)
    
    # Update attempt
    await db.quiz_attempts.update_one(
        {"id": attempt["id"]},
        {
            "$set": {
                "answers": answers_dict,
                "score": score,
                "passed": passed,
                "time_taken": submission.time_taken,
                "completed_at": datetime.now(timezone.utc),
                "is_completed": True
            }
        }
    )
    
    return {
        "attempt_id": attempt["id"],
        "score": score,
        "passed": passed,
        "correct_answers": correct_answers,
        "total_questions": total_questions,
        "passing_score": quiz.get("passing_score", 70),
        "time_taken": submission.time_taken,
        "detailed_results": detailed_results if quiz.get("show_results_immediately", True) else None
    }

@api_router.get("/quiz-attempts")
async def get_user_quiz_attempts(current_user: UserResponse = Depends(get_current_user)):
    """Get all quiz attempts for the current user"""
    attempts = await db.quiz_attempts.find({"user_id": current_user.id}).sort("started_at", -1).to_list(1000)
    
    # Enrich with quiz information
    enriched_attempts = []
    for attempt in attempts:
        quiz = await db.quizzes.find_one({"id": attempt["quiz_id"]})
        attempt_data = QuizAttempt(**attempt).dict()
        attempt_data["quiz_title"] = quiz.get("title", "Unknown Quiz") if quiz else "Unknown Quiz"
        attempt_data["quiz_type"] = quiz.get("quiz_type", "unknown") if quiz else "unknown"
        enriched_attempts.append(attempt_data)
    
    return enriched_attempts

@api_router.get("/quiz-attempts/{attempt_id}")
async def get_quiz_attempt_results(attempt_id: str, current_user: UserResponse = Depends(get_current_user)):
    """Get detailed results of a specific quiz attempt"""
    attempt = await db.quiz_attempts.find_one({"id": attempt_id, "user_id": current_user.id})
    if not attempt:
        raise HTTPException(status_code=404, detail="Quiz attempt not found")
    
    if not attempt.get("is_completed", False):
        raise HTTPException(status_code=400, detail="Quiz attempt not completed yet")
    
    # Get quiz and rebuild detailed results
    quiz = await db.quizzes.find_one({"id": attempt["quiz_id"]})
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    detailed_results = []
    answers_dict = attempt.get("answers", {})
    
    for question_id in quiz.get("question_ids", []):
        question = await db.questions.find_one({"id": question_id})
        if question:
            selected_option_id = answers_dict.get(question_id)
            correct_option = next((opt for opt in question["options"] if opt["is_correct"]), None)
            is_correct = selected_option_id == correct_option["id"] if correct_option else False
            
            detailed_results.append({
                "question_id": question_id,
                "question_text": question["question_text"],
                "selected_option_id": selected_option_id,
                "correct_option_id": correct_option["id"] if correct_option else None,
                "is_correct": is_correct,
                "options": question["options"],
                "explanation": question.get("explanation", "")
            })
    
    return {
        "attempt": QuizAttempt(**attempt).dict(),
        "quiz": Quiz(**quiz).dict(),
        "detailed_results": detailed_results
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
                "sections": [
                    {
                        "id": str(uuid.uuid4()),
                        "title": "1.1 ¿Qué es el Testing?",
                        "content": """
# ¿Qué es el Testing?

El testing de software es un proceso para evaluar y verificar que una aplicación de software hace lo que se supone que debe hacer. Los beneficios del testing incluyen:

## Objetivos del Testing
- **Prevenir defectos** mediante revisiones tempranas y análisis estático
- **Verificar** que se cumplen todos los requisitos especificados
- **Validar** que el sistema funciona como esperan los usuarios
- **Construir confianza** en el nivel de calidad del componente o sistema
- **Encontrar defectos** y fallas
- **Proporcionar información** para la toma de decisiones
- **Cumplir** con requisitos legales, contractuales o normativos

## Diferencias Clave
- **Error (Mistake)**: Acción humana que produce un resultado incorrecto
- **Defecto (Defect/Bug)**: Falta o imperfección en el código
- **Falla (Failure)**: Desviación del comportamiento esperado del sistema

El testing y la depuración son procesos diferentes. El testing puede mostrar la presencia de defectos, pero no puede probar su ausencia.
                        """,
                        "order": 1
                    },
                    {
                        "id": str(uuid.uuid4()),
                        "title": "1.2 Los Siete Principios del Testing",
                        "content": """
# Los Siete Principios del Testing

Los principios del testing proporcionan directrices generales comunes a todo tipo de testing.

## 1. El Testing Muestra la Presencia de Defectos, No su Ausencia
El testing puede mostrar que hay defectos presentes, pero no puede probar que no hay defectos.

## 2. Testing Exhaustivo es Imposible
Es imposible probar todo (todas las combinaciones de entradas y precondiciones), excepto en casos triviales.

## 3. Testing Temprano Ahorra Tiempo y Dinero
Las actividades de testing deben comenzar lo antes posible en el ciclo de vida del desarrollo.

## 4. Los Defectos se Agrupan
Un pequeño número de módulos contiene la mayoría de los defectos descubiertos durante las pruebas previas al lanzamiento.

## 5. Cuidado con la Paradoja del Pesticida
Si los mismos tests se repiten una y otra vez, eventualmente esos tests ya no encontrarán más defectos.

## 6. El Testing Depende del Contexto
El testing se hace de manera diferente en diferentes contextos.

## 7. La Falacia de la Ausencia de Errores
Encontrar y corregir defectos no ayuda si el sistema construido no cumple las expectativas del usuario.
                        """,
                        "order": 2
                    },
                    {
                        "id": str(uuid.uuid4()),
                        "title": "1.3 Proceso Fundamental de Testing",
                        "content": """
# Proceso Fundamental de Testing

El proceso fundamental de testing consiste en las siguientes actividades principales:

## Planificación del Testing
- Definir objetivos del testing
- Seleccionar enfoque del testing
- Determinar recursos necesarios
- Programar actividades de testing

## Monitoreo y Control del Testing
- Comparar progreso actual con el plan
- Tomar acciones correctivas cuando sea necesario
- Actualizar el plan basado en nueva información

## Análisis del Testing
- Analizar la base de testing
- Identificar características a probar
- Definir y priorizar condiciones de testing
- Capturar trazabilidad bidireccional

## Diseño del Testing
- Diseñar y priorizar casos de testing
- Identificar datos de testing necesarios
- Diseñar el entorno de testing
- Capturar trazabilidad bidireccional

## Implementación del Testing
- Desarrollar y priorizar procedimientos de testing
- Crear suites de testing
- Preparar datos de testing
- Preparar el entorno de testing

## Ejecución del Testing
- Ejecutar suites de testing
- Registrar resultados de la ejecución
- Comparar resultados actuales con esperados
- Reportar defectos
- Re-ejecutar testing después de correcciones

## Finalización del Testing
- Verificar que todos los productos de trabajo entregables han sido entregados
- Finalizar y archivar el entorno de testing
- Entregar productos de trabajo de testing al equipo de mantenimiento
- Analizar lecciones aprendidas
                        """,
                        "order": 3
                    }
                ],
                "order": 1,
                "estimated_time": 45,
                "learning_objectives": [
                    "Comprender qué es el testing y por qué es necesario",
                    "Conocer los 7 principios fundamentales del testing",
                    "Identificar las actividades del proceso de testing",
                    "Distinguir entre errores, defectos y fallas"
                ],
                "key_concepts": [
                    "Error, Defecto, Falla",
                    "Los 7 principios del testing",
                    "Proceso fundamental de testing",
                    "Objetivos del testing"
                ],
                "created_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "title": "2. Testing a lo largo del Ciclo de Vida del Software",
                "description": "Cómo se integra el testing en diferentes modelos de ciclo de vida del desarrollo.",
                "content": "Exploraremos cómo el testing se adapta a metodologías como Waterfall, Agile, y DevOps, y cómo las actividades de testing varían en cada fase.",
                "sections": [
                    {
                        "id": str(uuid.uuid4()),
                        "title": "2.1 Modelos de Ciclo de Vida del Software",
                        "content": """
# Modelos de Ciclo de Vida del Software en Testing

El testing debe adaptarse al modelo de ciclo de vida de desarrollo utilizado.

## Modelo Secuencial (Waterfall)
- **Características**: Fases secuenciales, documentación extensiva
- **Testing**: Se realiza después del desarrollo
- **Ventajas**: Planificación clara, fácil gestión
- **Desventajas**: Detección tardía de defectos, poca flexibilidad

## Modelo Iterativo e Incremental
- **Características**: Desarrollo en iteraciones, entrega incremental
- **Testing**: En cada iteración se testing y entrega funcionalidad
- **Ventajas**: Feedback temprano, adaptabilidad
- **Desventajas**: Requiere buena gestión de configuración

## Modelo en V
- **Características**: Para cada fase de desarrollo hay una fase de testing correspondiente
- **Testing**: Planificación temprana, ejecución tardía
- **Ventajas**: Planificación temprana del testing
- **Desventajas**: Rigidez similar al modelo waterfall
                        """,
                        "order": 1
                    },
                    {
                        "id": str(uuid.uuid4()),
                        "title": "2.2 Niveles de Testing",
                        "content": """
# Niveles de Testing

## Testing de Componente (Unit Testing)
- **Objetivo**: Verificar componentes individuales aisladamente
- **Alcance**: Funciones, objetos, clases
- **Responsable**: Desarrolladores
- **Herramientas**: Frameworks de unit testing

## Testing de Integración
- **Objetivo**: Verificar interfaces entre componentes
- **Tipos**: Big Bang, Incremental (Top-down, Bottom-up)
- **Alcance**: APIs, interfaces de base de datos
- **Responsable**: Desarrolladores o testers

## Testing de Sistema
- **Objetivo**: Verificar el comportamiento del sistema completo
- **Alcance**: Sistema completo en su entorno
- **Tipos**: Funcional, no funcional
- **Responsable**: Testers independientes

## Testing de Aceptación
- **Objetivo**: Verificar que el sistema cumple los requisitos del negocio
- **Tipos**: Aceptación del usuario, aceptación del negocio, aceptación contractual
- **Alcance**: Flujos de trabajo completos
- **Responsable**: Usuarios finales, clientes
                        """,
                        "order": 2
                    }
                ],
                "order": 2,
                "estimated_time": 50,
                "learning_objectives": [
                    "Entender diferentes modelos de ciclo de vida",
                    "Conocer los niveles de testing",
                    "Saber cuándo aplicar cada tipo de testing",
                    "Comprender el testing en metodologías ágiles"
                ],
                "key_concepts": [
                    "Modelo en V",
                    "Testing iterativo",
                    "Niveles de testing",
                    "Testing ágil"
                ],
                "created_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "title": "3. Técnicas de Testing Estático",
                "description": "Revisiones, walkthroughs, inspecciones y análisis estático de código.",
                "content": "Aprende sobre las técnicas de testing que no requieren ejecutar el código, incluyendo revisiones formales e informales.",
                "sections": [
                    {
                        "id": str(uuid.uuid4()),
                        "title": "3.1 Fundamentos del Testing Estático",
                        "content": """
# Testing Estático vs Testing Dinámico

## Testing Estático
- **Definición**: Examinar el código o documentación sin ejecutar el software
- **Métodos**: Revisiones, walkthroughs, inspecciones, análisis estático
- **Beneficios**: Detección temprana de defectos, costo-efectivo

## Testing Dinámico  
- **Definición**: Ejecutar el software con casos de testing
- **Métodos**: Testing funcional y no funcional
- **Beneficios**: Verificación del comportamiento real

## Diferencias Clave
- Testing estático encuentra **defectos directamente**
- Testing dinámico encuentra **fallas** que indican defectos
- Ambos son complementarios, no alternativos
                        """,
                        "order": 1
                    },
                    {
                        "id": str(uuid.uuid4()),
                        "title": "3.2 Proceso de Revisión",
                        "content": """
# Proceso de Revisión

## Tipos de Revisión

### Revisión Informal
- Sin proceso formal
- No requiere documentación
- Pair programming, buddy checks

### Walkthrough
- Autor guía a los participantes
- Escenarios de uso, dry runs
- Puede ser formal o informal

### Revisión Técnica
- Revisores técnicos expertos
- Sin gestor como líder
- Puede incluir peers, expertos técnicos

### Inspección
- Proceso más formal
- Roles definidos, métricas, checklists
- Basada en reglas y checklists

## Roles en la Revisión
- **Autor**: Creador del producto de trabajo
- **Gestor**: Planifica la revisión
- **Facilitador**: Modera la reunión
- **Revisor**: Identifica anomalías
- **Secretario**: Documenta la reunión
                        """,
                        "order": 2
                    }
                ],
                "order": 3,
                "estimated_time": 40,
                "learning_objectives": [
                    "Distinguir entre testing estático y dinámico",
                    "Conocer diferentes tipos de revisión",
                    "Entender el proceso de revisión",
                    "Aplicar técnicas de análisis estático"
                ],
                "key_concepts": [
                    "Testing estático",
                    "Tipos de revisión", 
                    "Proceso de revisión",
                    "Análisis estático de código"
                ],
                "created_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "title": "4. Técnicas de Diseño de Pruebas",
                "description": "Técnicas de caja negra, caja blanca y basadas en la experiencia.",
                "content": "Domina las técnicas para diseñar casos de prueba efectivos, incluyendo partición de equivalencia, análisis de valores límite y más.",
                "sections": [
                    {
                        "id": str(uuid.uuid4()),
                        "title": "4.1 Técnicas de Caja Negra",
                        "content": """
# Técnicas de Caja Negra (Black-box)

Las técnicas de caja negra se basan en especificaciones, requisitos o funcionalidad, sin conocimiento de la estructura interna.

## Partición de Equivalencia
- **Concepto**: Dividir datos de entrada en particiones
- **Objetivo**: Reducir número de casos de testing
- **Aplicación**: Una prueba por partición válida, una por inválida

### Ejemplo Práctico
Para un campo edad (18-65 años):
- Partición válida: 18-65
- Particiones inválidas: <18, >65

## Análisis de Valores Límite
- **Concepto**: Probar valores en los límites de las particiones
- **Razón**: Los defectos ocurren frecuentemente en los límites
- **Aplicación**: Probar límite inferior, superior, y valores adyacentes

### Ejemplo Práctico  
Para rango 18-65:
- Valores a probar: 17, 18, 19, 64, 65, 66

## Tablas de Decisión
- **Uso**: Cuando el comportamiento depende de combinaciones de condiciones
- **Estructura**: Condiciones, acciones, reglas
- **Beneficio**: Cobertura sistemática de combinaciones

## Testing de Transición de Estados
- **Aplicación**: Sistemas con estados y transiciones
- **Elementos**: Estados, transiciones, eventos, acciones
- **Cobertura**: Estados válidos, transiciones válidas, secuencias
                        """,
                        "order": 1
                    },
                    {
                        "id": str(uuid.uuid4()),
                        "title": "4.2 Técnicas de Caja Blanca",
                        "content": """
# Técnicas de Caja Blanca (White-box)

Las técnicas de caja blanca se basan en la estructura interna del código.

## Cobertura de Sentencias
- **Objetivo**: Ejecutar todas las sentencias del código
- **Medición**: % de sentencias ejecutadas
- **Mínimo**: Nivel básico de cobertura

## Cobertura de Decisiones/Ramas
- **Objetivo**: Ejecutar todos los resultados posibles de decisiones
- **Medición**: % de ramas ejecutadas  
- **Superior**: Más fuerte que cobertura de sentencias

## Cobertura de Condiciones
- **Objetivo**: Probar cada condición booleana
- **Aplicación**: Condiciones individuales dentro de decisiones
- **Detalle**: Más granular que cobertura de decisiones

## Ejemplo Práctico
```python
if (a > 5) and (b < 10):  # Decisión con 2 condiciones
    statement1()          # Rama verdadera
else:
    statement2()          # Rama falsa
```

**Cobertura de sentencias**: Ejecutar statement1() O statement2()
**Cobertura de decisiones**: Ejecutar AMBAS ramas
**Cobertura de condiciones**: Probar a>5 (True/False) Y b<10 (True/False)
                        """,
                        "order": 2
                    }
                ],
                "order": 4,
                "estimated_time": 60,
                "learning_objectives": [
                    "Aplicar técnicas de caja negra",
                    "Utilizar análisis de valores límite",
                    "Crear tablas de decisión",
                    "Entender cobertura de código"
                ],
                "key_concepts": [
                    "Partición de equivalencia",
                    "Valores límite",
                    "Tablas de decisión",
                    "Cobertura de código"
                ],
                "created_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "title": "5. Gestión de las Pruebas",
                "description": "Planificación, estimación, monitoreo y control de las actividades de testing.",
                "content": "Aprende a crear planes de prueba, estimar esfuerzo, gestionar riesgos y reportar el progreso del testing.",
                "sections": [
                    {
                        "id": str(uuid.uuid4()),
                        "title": "5.1 Organización del Testing",
                        "content": """
# Organización del Testing

## Independencia del Testing
- **Nivel 1**: Sin testers independientes (desarrolladores prueban su código)
- **Nivel 2**: Testers independientes dentro del equipo de desarrollo  
- **Nivel 3**: Equipo de testing independiente reportando a gestión del proyecto
- **Nivel 4**: Testers independientes de organización externa

## Beneficios de la Independencia
- Reconocer diferentes tipos de fallas
- Verificar asunciones hechas durante especificación e implementación
- Perspectiva objetiva

## Desventajas Potenciales
- Aislamiento del equipo de desarrollo
- Posible retraso en feedback
- Desarrolladores pueden perder responsabilidad por calidad

## Roles y Responsabilidades

### Test Manager
- Planificación general del testing
- Escribir o revisar política y estrategia de testing
- Coordinar el testing con gestores de proyecto, propietarios de producto

### Tester
- Revisar y contribuir a planes de testing
- Analizar, revisar y evaluar requisitos y especificaciones
- Diseñar, implementar y ejecutar casos de testing
                        """,
                        "order": 1
                    },
                    {
                        "id": str(uuid.uuid4()),
                        "title": "5.2 Planificación y Estimación",
                        "content": """
# Planificación y Estimación del Testing

## Propósito y Contenido del Plan de Testing
Un plan de testing documenta los medios y cronograma para alcanzar los objetivos de testing.

### Contenido Típico:
- **Alcance**: Qué será y no será probado
- **Enfoque**: Niveles de testing, tipos de testing, técnicas
- **Recursos**: Personas, herramientas, entorno
- **Cronograma**: Cuándo ocurrirán las actividades de testing

## Estrategia de Testing
Define el enfoque general del testing para el proyecto.

### Tipos de Estrategia:
- **Analítica**: Basada en análisis de factores como requisitos o riesgos
- **Basada en Modelos**: Basada en modelos del sistema
- **Metódica**: Sistemática, usando checklists predefinidos
- **Reactiva**: Reactiva a eventos durante ejecución del testing
- **Dirigida**: Dirigida por stakeholders principales
- **Regresiva**: Reutilización de material de testing existente

## Técnicas de Estimación

### Estimación Basada en Métricas
- Usar datos históricos de proyectos similares
- Métricas: productividad, ratios de defectos

### Estimación Basada en Expertos
- Consultar con expertos en el dominio
- Técnica Wideband Delphi

### Estimación de Tres Puntos
- Optimista, pesimista, más probable
- Fórmula: (Optimista + 4*Más Probable + Pesimista) / 6
                        """,
                        "order": 2
                    }
                ],
                "order": 5,
                "estimated_time": 55,
                "learning_objectives": [
                    "Entender organización del testing",
                    "Crear planes de testing efectivos",
                    "Aplicar técnicas de estimación",
                    "Gestionar riesgos del testing"
                ],
                "key_concepts": [
                    "Independencia del testing",
                    "Plan de testing",
                    "Estrategia de testing",
                    "Estimación de esfuerzo"
                ],
                "created_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "title": "6. Herramientas para el Testing",
                "description": "Clasificación y uso de herramientas de apoyo al testing.",
                "content": "Conoce las diferentes categorías de herramientas de testing y cómo pueden mejorar la eficiencia y efectividad de tus pruebas.",
                "sections": [
                    {
                        "id": str(uuid.uuid4()),
                        "title": "6.1 Clasificación de Herramientas",
                        "content": """
# Clasificación de Herramientas de Testing

## Herramientas de Gestión de Testing
- **Test Management Tools**: Planificación, seguimiento, gestión de casos
- **ALM Tools**: Application Lifecycle Management
- **Ejemplos**: TestRail, Zephyr, Azure DevOps

## Herramientas de Testing Estático
- **Análisis Estático**: Revisión automatizada de código
- **Linters**: Verificación de estándares de codificación  
- **Ejemplos**: SonarQube, ESLint, Checkstyle

## Herramientas de Diseño e Implementación
- **Model-Based Testing**: Generación desde modelos
- **Test Data Preparation**: Creación de datos de testing
- **Ejemplos**: Conformiq, Toad Data Point

## Herramientas de Ejecución y Logging
- **Test Execution**: Automatización de ejecución
- **Test Harnesses**: Frameworks de ejecución
- **Comparadores**: Verificación de resultados
- **Coverage Tools**: Medición de cobertura

## Herramientas de Rendimiento y Monitoreo
- **Load Testing**: Simulación de carga
- **Performance Monitoring**: Monitoreo en tiempo real
- **Ejemplos**: JMeter, LoadRunner, New Relic
                        """,
                        "order": 1
                    },
                    {
                        "id": str(uuid.uuid4()),
                        "title": "6.2 Beneficios y Riesgos de la Automatización",
                        "content": """
# Automatización del Testing

## Beneficios de la Automatización
- **Eficiencia**: Ejecución más rápida de tests repetitivos
- **Consistencia**: Ejecución idéntica cada vez
- **Cobertura**: Posibilidad de mayor cobertura
- **Reutilización**: Scripts reutilizables
- **Precisión**: Reducción de errores humanos

## Limitaciones y Riesgos
- **Inversión Inicial**: Costo alto de implementación
- **Mantenimiento**: Scripts requieren actualización constante
- **Falsa Seguridad**: Automatización no garantiza calidad
- **Herramientas Complejas**: Curva de aprendizaje
- **No Todo es Automatizable**: Usabilidad, experiencia de usuario

## Factores de Éxito para Automatización
- **Tests Repetitivos**: Alto valor para automatización
- **Casos Estables**: Funcionalidad que no cambia frecuentemente
- **Datos Consistentes**: Disponibilidad de datos de testing
- **ROI Claro**: Retorno de inversión justificable

## Pirámide de Testing
- **Base**: Unit Tests (muchos, rápidos, baratos)
- **Medio**: Integration Tests (algunos, moderados)  
- **Tope**: UI Tests (pocos, lentos, caros)

## Estrategia de Automatización
1. **Evaluar** aplicación y casos de testing
2. **Seleccionar** herramient apropiada
3. **Diseñar** arquitectura de automatización
4. **Implementar** scripts mantenibles
5. **Ejecutar** y mantener suite de testing
                        """,
                        "order": 2
                    }
                ],
                "order": 6,
                "estimated_time": 35,
                "learning_objectives": [
                    "Clasificar herramientas de testing",
                    "Evaluar beneficios de automatización",
                    "Seleccionar herramientas apropiadas",
                    "Implementar estrategia de automatización"
                ],
                "key_concepts": [
                    "Tipos de herramientas",
                    "Automatización de testing",
                    "ROI de automatización",
                    "Pirámide de testing"
                ],
                "created_at": datetime.now(timezone.utc)
            }
        ]
        
        await db.istqb_modules.insert_many(sample_modules)
        logger.info("Sample ISTQB modules created")
        
        # Create sample questions if they don't exist
        existing_questions = await db.questions.count_documents({})
        if existing_questions == 0:
            # Get first module ID for questions
            first_module = sample_modules[0]
            module_id = first_module["id"]
            section_id = first_module["sections"][0]["id"]
            
            sample_questions = [
                {
                    "id": str(uuid.uuid4()),
                    "module_id": module_id,
                    "section_id": section_id,
                    "question_text": "¿Cuál de los siguientes NO es uno de los 7 principios fundamentales del testing según ISTQB?",
                    "question_type": "multiple_choice",
                    "options": [
                        {
                            "id": str(uuid.uuid4()),
                            "text": "El testing muestra la presencia de defectos, no su ausencia",
                            "is_correct": False,
                            "explanation": "Este es el principio #1 del testing"
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "text": "Testing exhaustivo es imposible",
                            "is_correct": False,
                            "explanation": "Este es el principio #2 del testing"
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "text": "El testing garantiza software libre de defectos",
                            "is_correct": True,
                            "explanation": "Correcto. Este NO es un principio del testing. El testing no puede garantizar software libre de defectos."
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "text": "Testing temprano ahorra tiempo y dinero",
                            "is_correct": False,
                            "explanation": "Este es el principio #3 del testing"
                        }
                    ],
                    "difficulty": "medium",
                    "topic": "Principios del Testing",
                    "explanation": "El testing no puede probar la ausencia de defectos, solo puede mostrar que están presentes. Nunca puede garantizar software completamente libre de defectos.",
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "id": str(uuid.uuid4()),
                    "module_id": module_id,
                    "section_id": section_id,
                    "question_text": "¿Qué diferencia hay entre un ERROR, un DEFECTO y una FALLA?",
                    "question_type": "multiple_choice",
                    "options": [
                        {
                            "id": str(uuid.uuid4()),
                            "text": "Son términos sinónimos que se refieren a lo mismo",
                            "is_correct": False,
                            "explanation": "No son sinónimos, cada término tiene un significado específico"
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "text": "Error es la acción humana, Defecto es la imperfección en el código, Falla es la desviación del comportamiento esperado",
                            "is_correct": True,
                            "explanation": "Correcto. Error (mistake) → Defecto (defect/bug) → Falla (failure) es la secuencia lógica."
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "text": "Falla es lo más grave, luego Defecto, luego Error",
                            "is_correct": False,
                            "explanation": "No se trata de gravedad sino de la secuencia causal"
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "text": "Solo importa identificar las Fallas, no los Errores ni Defectos",
                            "is_correct": False,
                            "explanation": "Es importante entender toda la cadena causal para prevenir problemas"
                        }
                    ],
                    "difficulty": "easy",
                    "topic": "Terminología del Testing",
                    "explanation": "La secuencia es: Error humano → genera un Defecto en el código → que puede causar una Falla en la ejecución.",
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "id": str(uuid.uuid4()),
                    "module_id": module_id,
                    "section_id": section_id,
                    "question_text": "¿Por qué es importante comenzar las actividades de testing lo antes posible en el ciclo de vida del desarrollo?",
                    "question_type": "multiple_choice",
                    "options": [
                        {
                            "id": str(uuid.uuid4()),
                            "text": "Para ocupar a los testers mientras los desarrolladores terminan el código",
                            "is_correct": False,
                            "explanation": "Esta no es la razón del testing temprano"
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "text": "Porque es más barato encontrar y corregir defectos en etapas tempranas",
                            "is_correct": True,
                            "explanation": "Correcto. Este es el principio #3: Testing temprano ahorra tiempo y dinero."
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "text": "Para poder hacer testing exhaustivo de todo el sistema",
                            "is_correct": False,
                            "explanation": "El testing exhaustivo es imposible según el principio #2"
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "text": "Para eliminar completamente todos los defectos del software",
                            "is_correct": False,
                            "explanation": "El testing no puede probar la ausencia de defectos"
                        }
                    ],
                    "difficulty": "medium",
                    "topic": "Testing Temprano",
                    "explanation": "Cuanto más tarde se encuentra un defecto en el ciclo de desarrollo, más costoso es corregirlo. Los defectos encontrados en producción pueden costar 100 veces más que los encontrados en desarrollo.",
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "id": str(uuid.uuid4()),
                    "module_id": module_id,
                    "section_id": section_id,
                    "question_text": "¿Qué significa la 'Paradoja del Pesticida' en testing?",
                    "question_type": "multiple_choice",
                    "options": [
                        {
                            "id": str(uuid.uuid4()),
                            "text": "Que el testing es tóxico para el desarrollo de software",
                            "is_correct": False,
                            "explanation": "No tiene que ver con toxicidad literal"
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "text": "Que si los mismos tests se repiten constantemente, eventualmente dejarán de encontrar defectos",
                            "is_correct": True,
                            "explanation": "Correcto. Como los pesticidas pierden efectividad, los tests repetitivos también."
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "text": "Que algunos bugs son inmunes a las pruebas",
                            "is_correct": False,
                            "explanation": "No se trata de inmunidad sino de repetición"
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "text": "Que hacer testing mata la creatividad de los desarrolladores",
                            "is_correct": False,
                            "explanation": "Esta no es la analogía correcta"
                        }
                    ],
                    "difficulty": "medium",
                    "topic": "Principios del Testing",
                    "explanation": "Los tests deben evolucionar y actualizarse. Si siempre ejecutamos los mismos tests, encontraremos los mismos bugs pero no los nuevos.",
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "id": str(uuid.uuid4()),
                    "module_id": module_id,
                    "section_id": section_id,
                    "question_text": "¿Cuáles son los principales objetivos del testing de software?",
                    "question_type": "multiple_choice",
                    "options": [
                        {
                            "id": str(uuid.uuid4()),
                            "text": "Solo encontrar bugs y reportarlos",
                            "is_correct": False,
                            "explanation": "El testing tiene objetivos más amplios que solo encontrar bugs"
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "text": "Prevenir defectos, verificar requisitos, validar funcionalidad y construir confianza",
                            "is_correct": True,
                            "explanation": "Correcto. Estos son los principales objetivos del testing según ISTQB."
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "text": "Retrasar el lanzamiento del producto hasta que sea perfecto",
                            "is_correct": False,
                            "explanation": "El testing busca equilibrio entre calidad y tiempo de entrega"
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "text": "Demostrar que el software no tiene ningún defecto",
                            "is_correct": False,
                            "explanation": "El testing no puede probar la ausencia de defectos"
                        }
                    ],
                    "difficulty": "easy",
                    "topic": "Objetivos del Testing",
                    "explanation": "El testing tiene múltiples objetivos: prevenir defectos mediante revisiones tempranas, verificar que se cumplen los requisitos, validar que funciona como esperan los usuarios, y construir confianza en la calidad.",
                    "created_at": datetime.now(timezone.utc)
                }
            ]
            
            await db.questions.insert_many(sample_questions)
            logger.info("Sample questions created")
            
            # Create sample quizzes
            question_ids = [q["id"] for q in sample_questions]
            
            sample_quizzes = [
                {
                    "id": str(uuid.uuid4()),
                    "title": "Fundamentos del Testing - Práctica",
                    "description": "Quiz de práctica sobre los conceptos básicos del testing de software",
                    "module_id": module_id,
                    "quiz_type": "practice",
                    "question_ids": question_ids,
                    "time_limit": 15,  # 15 minutes
                    "passing_score": 70,
                    "randomize_questions": True,
                    "randomize_options": True,
                    "show_results_immediately": True,
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "id": str(uuid.uuid4()),
                    "title": "Examen Módulo 1 - Fundamentos",
                    "description": "Examen formal del módulo 1: Fundamentos de las Pruebas",
                    "module_id": module_id,
                    "quiz_type": "module_test",
                    "question_ids": question_ids,
                    "time_limit": 20,  # 20 minutes
                    "passing_score": 75,
                    "randomize_questions": True,
                    "randomize_options": True,
                    "show_results_immediately": True,
                    "created_at": datetime.now(timezone.utc)
                }
            ]
            
            await db.quizzes.insert_many(sample_quizzes)
            logger.info("Sample quizzes created")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()