# 🛠️ Guía de Desarrollo Continuado - ISTQB Platform

## 🎯 Para Desarrolladores que Continúan el Proyecto

Esta guía te permitirá continuar el desarrollo del proyecto ISTQB Study Platform desde donde se quedó.

---

## 🚀 Setup Inicial Rápido

### 1. Verificar Estado del Sistema
```bash
# Verificar servicios
sudo supervisorctl status

# Si no están corriendo
sudo supervisorctl restart all

# Verificar logs si hay problemas
tail -f /var/log/supervisor/backend.err.log
tail -f /var/log/supervisor/frontend.err.log
```

### 2. Acceso a la Aplicación
- **Frontend**: URL en `/app/frontend/.env` (REACT_APP_BACKEND_URL)
- **Backend API**: `{FRONTEND_URL}/api`
- **MongoDB**: localhost:27017

### 3. Credenciales de Prueba
```javascript
// Crear un usuario de prueba
const testUser = {
  email: "admin@istqb.com",
  password: "admin123",
  full_name: "Admin ISTQB"
}
```

---

## 📋 Plan de Desarrollo por Prioridades

### 🥇 PRIORIDAD ALTA - Sistema de Cuestionarios

#### Paso 1: Crear Modelos de Preguntas
```python
# Agregar a server.py después de UserProgress

class Question(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    module_id: str
    section_id: Optional[str] = None
    question_text: str
    question_type: str = "multiple_choice"  # multiple_choice, true_false
    options: List[str] = Field(default_factory=list)  # ["A) ...", "B) ...", ...]
    correct_answer: int  # Índice de la respuesta correcta (0-3)
    explanation: str
    difficulty: str = "medium"  # easy, medium, hard
    points: int = 1
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class QuizSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    module_id: str
    quiz_type: str = "practice"  # practice, exam, final
    questions: List[str] = Field(default_factory=list)  # Question IDs
    current_question: int = 0
    answers: Dict[str, int] = Field(default_factory=dict)  # question_id: selected_option
    score: int = 0
    total_questions: int = 0
    correct_answers: int = 0
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    time_limit: Optional[int] = None  # en minutos
    is_completed: bool = False
```

#### Paso 2: Crear Endpoints de Cuestionarios
```python
# Agregar después de los endpoints existentes

@api_router.get("/modules/{module_id}/questions", response_model=List[Question])
async def get_module_questions(module_id: str, limit: int = 10):
    questions = await db.questions.find({"module_id": module_id}).limit(limit).to_list(limit)
    return [Question(**q) for q in questions]

@api_router.post("/quiz/start/{module_id}")
async def start_quiz(
    module_id: str, 
    quiz_type: str = "practice",
    question_count: int = 10,
    current_user: UserResponse = Depends(get_current_user)
):
    # Obtener preguntas random del módulo
    questions = await db.questions.find({"module_id": module_id}).to_list(1000)
    selected_questions = random.sample(questions, min(question_count, len(questions)))
    
    quiz_session = QuizSession(
        user_id=current_user.id,
        module_id=module_id,
        quiz_type=quiz_type,
        questions=[q["id"] for q in selected_questions],
        total_questions=len(selected_questions),
        time_limit=30 if quiz_type == "exam" else None
    )
    
    await db.quiz_sessions.insert_one(quiz_session.dict())
    return {"quiz_id": quiz_session.id, "total_questions": quiz_session.total_questions}

@api_router.post("/quiz/{quiz_id}/answer")
async def submit_answer(
    quiz_id: str,
    question_id: str,
    selected_option: int,
    current_user: UserResponse = Depends(get_current_user)
):
    # Actualizar respuesta en la sesión
    await db.quiz_sessions.update_one(
        {"id": quiz_id, "user_id": current_user.id},
        {"$set": {f"answers.{question_id}": selected_option}}
    )
    return {"message": "Answer recorded"}

@api_router.post("/quiz/{quiz_id}/complete")
async def complete_quiz(quiz_id: str, current_user: UserResponse = Depends(get_current_user)):
    quiz = await db.quiz_sessions.find_one({"id": quiz_id, "user_id": current_user.id})
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Calcular puntuación
    correct_count = 0
    total_points = 0
    
    for question_id, selected_option in quiz["answers"].items():
        question = await db.questions.find_one({"id": question_id})
        if question and question["correct_answer"] == selected_option:
            correct_count += 1
            total_points += question.get("points", 1)
    
    # Actualizar sesión
    await db.quiz_sessions.update_one(
        {"id": quiz_id},
        {"$set": {
            "score": total_points,
            "correct_answers": correct_count,
            "is_completed": True,
            "completed_at": datetime.now(timezone.utc)
        }}
    )
    
    return {
        "score": total_points,
        "correct_answers": correct_count,
        "total_questions": quiz["total_questions"],
        "percentage": round((correct_count / quiz["total_questions"]) * 100, 1)
    }
```

#### Paso 3: Crear Preguntas de Ejemplo
```python
# Agregar al startup_event después de crear los módulos

async def create_sample_questions():
    existing_questions = await db.questions.count_documents({})
    if existing_questions == 0:
        # Obtener IDs de módulos
        modules = await db.istqb_modules.find().to_list(100)
        
        sample_questions = []
        
        # Preguntas para Módulo 1 - Fundamentos
        if modules:
            module1_id = modules[0]["id"]
            questions_module1 = [
                {
                    "id": str(uuid.uuid4()),
                    "module_id": module1_id,
                    "question_text": "¿Cuál de los siguientes NO es uno de los 7 principios fundamentales del testing?",
                    "options": [
                        "A) El testing muestra la presencia de defectos",
                        "B) Testing exhaustivo es posible",
                        "C) Testing temprano ahorra tiempo y dinero", 
                        "D) Los defectos se agrupan"
                    ],
                    "correct_answer": 1,  # B es incorrecta
                    "explanation": "El testing exhaustivo es IMPOSIBLE, no posible. Este es el principio #2 del ISTQB.",
                    "difficulty": "easy"
                },
                {
                    "id": str(uuid.uuid4()),
                    "module_id": module1_id,
                    "question_text": "¿Qué significa que 'el testing depende del contexto'?",
                    "options": [
                        "A) Todos los proyectos se testean igual",
                        "B) El testing se hace diferente según el tipo de aplicación",
                        "C) Solo se aplica a aplicaciones web",
                        "D) No tiene importancia práctica"
                    ],
                    "correct_answer": 1,
                    "explanation": "El principio #6 establece que el testing se hace de manera diferente en diferentes contextos (web, móvil, crítico, etc.).",
                    "difficulty": "medium"
                }
            ]
            sample_questions.extend(questions_module1)
        
        if sample_questions:
            await db.questions.insert_many(sample_questions)
            logger.info(f"Created {len(sample_questions)} sample questions")

# Llamar en startup_event
await create_sample_questions()
```

#### Paso 4: Componente React para Quiz
```javascript
// Crear /app/frontend/src/components/QuizComponent.js

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Progress } from './ui/progress';
import { Clock, CheckCircle, X } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const QuizComponent = () => {
  const { moduleId } = useParams();
  const [quizSession, setQuizSession] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [timeLeft, setTimeLeft] = useState(null);
  const [isCompleted, setIsCompleted] = useState(false);
  const [results, setResults] = useState(null);
  
  const navigate = useNavigate();

  useEffect(() => {
    startQuiz();
  }, [moduleId]);

  const startQuiz = async () => {
    try {
      const response = await axios.post(`${API}/quiz/start/${moduleId}`, {
        quiz_type: 'practice',
        question_count: 10
      });
      
      const questionsResponse = await axios.get(`${API}/modules/${moduleId}/questions`);
      
      setQuizSession(response.data);
      setQuestions(questionsResponse.data.slice(0, response.data.total_questions));
    } catch (error) {
      console.error('Error starting quiz:', error);
    }
  };

  const selectAnswer = async (questionId, optionIndex) => {
    setSelectedAnswers(prev => ({
      ...prev,
      [questionId]: optionIndex
    }));

    try {
      await axios.post(`${API}/quiz/${quizSession.quiz_id}/answer`, {
        question_id: questionId,
        selected_option: optionIndex
      });
    } catch (error) {
      console.error('Error submitting answer:', error);
    }
  };

  const completeQuiz = async () => {
    try {
      const response = await axios.post(`${API}/quiz/${quizSession.quiz_id}/complete`);
      setResults(response.data);
      setIsCompleted(true);
    } catch (error) {
      console.error('Error completing quiz:', error);
    }
  };

  const nextQuestion = () => {
    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    } else {
      completeQuiz();
    }
  };

  if (isCompleted && results) {
    return (
      <div className="max-w-2xl mx-auto p-6">
        <Card>
          <CardHeader className="text-center">
            <CardTitle className="text-2xl">¡Quiz Completado!</CardTitle>
          </CardHeader>
          <CardContent className="text-center space-y-4">
            <div className="text-4xl font-bold text-blue-600">
              {results.percentage}%
            </div>
            <p className="text-lg">
              {results.correct_answers} de {results.total_questions} respuestas correctas
            </p>
            <div className="flex justify-center space-x-4">
              <Button onClick={() => navigate('/')}>
                Volver al Dashboard
              </Button>
              <Button variant="outline" onClick={() => window.location.reload()}>
                Intentar de Nuevo
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!questions.length) {
    return <div className="flex justify-center p-8">Cargando quiz...</div>;
  }

  const question = questions[currentQuestion];
  const progress = ((currentQuestion + 1) / questions.length) * 100;

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-6">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm text-gray-600">
            Pregunta {currentQuestion + 1} de {questions.length}
          </span>
          {timeLeft && (
            <span className="flex items-center text-sm text-gray-600">
              <Clock className="h-4 w-4 mr-1" />
              {Math.floor(timeLeft / 60)}:{(timeLeft % 60).toString().padStart(2, '0')}
            </span>
          )}
        </div>
        <Progress value={progress} className="h-2" />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-xl">{question.question_text}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {question.options.map((option, index) => (
              <button
                key={index}
                onClick={() => selectAnswer(question.id, index)}
                className={`w-full p-4 text-left border rounded-lg transition-colors ${
                  selectedAnswers[question.id] === index
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                {option}
              </button>
            ))}
          </div>
          
          <div className="flex justify-between mt-6">
            <Button
              variant="outline"
              onClick={() => setCurrentQuestion(Math.max(0, currentQuestion - 1))}
              disabled={currentQuestion === 0}
            >
              Anterior
            </Button>
            
            <Button
              onClick={nextQuestion}
              disabled={selectedAnswers[question.id] === undefined}
            >
              {currentQuestion === questions.length - 1 ? 'Finalizar' : 'Siguiente'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default QuizComponent;
```

#### Paso 5: Agregar Ruta de Quiz
```javascript
// En App.js, agregar la ruta
import QuizComponent from './components/QuizComponent';

// En las Routes
<Route path="/quiz/:moduleId" element={
  <ProtectedRoute>
    <QuizComponent />
  </ProtectedRoute>
} />
```

#### Paso 6: Agregar Botón de Quiz al Dashboard
```javascript
// En Dashboard component, en el mapeo de módulos agregar:
<div className="flex space-x-2">
  <Button 
    variant={isCompleted ? "secondary" : "default"}
    onClick={() => navigate(`/study/${module.id}`)}
  >
    {isCompleted ? "Revisar" : "Estudiar"}
  </Button>
  <Button 
    variant="outline"
    onClick={() => navigate(`/quiz/${module.id}`)}
  >
    Quiz
  </Button>
</div>
```

---

### 🥈 PRIORIDAD MEDIA - Gestión de Documentos PDF

#### Paso 1: Instalar Dependencias
```bash
# Backend
pip install python-multipart aiofiles

# Frontend  
cd frontend
yarn add react-pdf
```

#### Paso 2: Modelo y Endpoints para Documentos
```python
# Modelo Document
class Document(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    filename: str
    file_path: str
    module_id: Optional[str] = None
    uploaded_by: str
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    file_size: int
    content_type: str = "application/pdf"

# Endpoints
from fastapi import UploadFile, File
import aiofiles
import os

@api_router.post("/documents/upload")
async def upload_document(
    title: str,
    module_id: str = None,
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user)
):
    # Validar que sea PDF
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files allowed")
    
    # Crear directorio si no existe
    upload_dir = "/app/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generar nombre único
    file_id = str(uuid.uuid4())
    file_path = f"{upload_dir}/{file_id}_{file.filename}"
    
    # Guardar archivo
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # Crear documento en DB
    document = Document(
        title=title,
        filename=file.filename,
        file_path=file_path,
        module_id=module_id,
        uploaded_by=current_user.id,
        file_size=len(content)
    )
    
    await db.documents.insert_one(document.dict())
    return document

@api_router.get("/documents", response_model=List[Document])
async def get_documents(module_id: str = None, current_user: UserResponse = Depends(get_current_user)):
    filter_dict = {}
    if module_id:
        filter_dict["module_id"] = module_id
    
    documents = await db.documents.find(filter_dict).to_list(100)
    return [Document(**doc) for doc in documents]
```

---

### 🥉 PRIORIDAD BAJA - Funciones Avanzadas

#### Integración con IA (OpenAI)
```python
# Instalar: pip install openai
import openai

async def generate_questions_ai(module_content: str, count: int = 5):
    prompt = f"""
    Basándote en el siguiente contenido del módulo ISTQB, genera {count} preguntas de opción múltiple:
    
    {module_content}
    
    Formato JSON:
    {{
        "questions": [
            {{
                "question": "Pregunta aquí?",
                "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
                "correct": 0,
                "explanation": "Explicación de por qué es correcta"
            }}
        ]
    }}
    """
    
    response = await openai.ChatCompletion.acreate(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content
```

---

## 🐛 Debugging y Troubleshooting

### Errores Comunes

#### Backend No Inicia
```bash
# Verificar logs
tail -f /var/log/supervisor/backend.err.log

# Problemas comunes:
# - Dependencias faltantes: pip install -r requirements.txt
# - Puerto ocupado: cambiar puerto en supervisor
# - MongoDB no conecta: verificar MONGO_URL en .env
```

#### Frontend No Carga
```bash
# Verificar logs  
tail -f /var/log/supervisor/frontend.err.log

# Problemas comunes:
# - Dependencias: yarn install
# - Variable REACT_APP_BACKEND_URL incorrecta
# - CORS errors: verificar backend CORS_ORIGINS
```

#### Base de Datos
```bash
# Conectar a MongoDB
mongo mongodb://localhost:27017/istqb_platform

# Ver colecciones
show collections

# Ver usuarios
db.users.find()

# Ver módulos
db.istqb_modules.find()
```

---

## 📈 Métricas de Progreso

### Cómo Medir el Éxito
- **Módulos completados** por usuario
- **Tiempo promedio** por módulo
- **Puntuación** en quizzes
- **Retención** de usuarios
- **Tasa de aprobación** en exámenes

### Implementar Analytics Básico
```python
class UserActivity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    action: str  # login, start_module, complete_quiz, etc.
    details: Dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Endpoint para analytics
@api_router.post("/analytics/track")
async def track_activity(
    action: str,
    details: Dict = {},
    current_user: UserResponse = Depends(get_current_user)
):
    activity = UserActivity(
        user_id=current_user.id,
        action=action,
        details=details
    )
    await db.user_activities.insert_one(activity.dict())
    return {"message": "Activity tracked"}
```

---

## 🎯 Roadmap de Funcionalidades

### Sprint 1 (1-2 semanas)
- [ ] Sistema de cuestionarios básico
- [ ] 50+ preguntas para todos los módulos
- [ ] Resultados y estadísticas de quiz

### Sprint 2 (1-2 semanas)  
- [ ] Upload y gestión de PDFs
- [ ] Visor de PDF integrado
- [ ] Organización por módulos

### Sprint 3 (2-3 semanas)
- [ ] Simulacros de examen completos
- [ ] Timer y condiciones de examen real
- [ ] Certificados de completación

### Sprint 4 (2-3 semanas)
- [ ] Integración con IA para generar preguntas
- [ ] Analytics avanzado
- [ ] Recomendaciones personalizadas

---

## 💡 Tips de Desarrollo

### Mejores Prácticas
1. **Siempre probar con el testing agent** después de cambios en backend
2. **Mantener test_result.md actualizado** con nuevas funcionalidades
3. **Hacer commits frecuentes** con mensajes descriptivos
4. **Documentar nuevas APIs** en esta guía
5. **Hacer backup de la BD** antes de cambios grandes

### Herramientas Útiles
```bash
# Ver logs en tiempo real
tail -f /var/log/supervisor/backend.out.log
tail -f /var/log/supervisor/frontend.out.log

# Restart solo un servicio
sudo supervisorctl restart backend
sudo supervisorctl restart frontend

# MongoDB queries útiles
mongo istqb_platform --eval "db.users.count()"
mongo istqb_platform --eval "db.istqb_modules.find().count()"
```

---

## 🆘 Contacto y Ayuda

### Si Te Atascas
1. **Revisar logs** primero
2. **Consultar esta documentación**
3. **Probar en ambiente limpio**
4. **Buscar en Stack Overflow**
5. **Consultar documentación oficial** de FastAPI/React

### Recursos de la Comunidad
- **ISTQB Official**: https://www.istqb.org/
- **FastAPI Community**: https://github.com/tiangolo/fastapi
- **React Community**: https://reactjs.org/community/support.html

---

**¡Éxito en tu desarrollo! 🚀**

*Esta plataforma ya tiene una base sólida. Solo necesitas agregar las funcionalidades que más valor aporten a tus usuarios.*