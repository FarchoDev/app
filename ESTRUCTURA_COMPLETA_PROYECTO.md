# 📁 Estructura Completa del Proyecto ISTQB

## 🗂️ Árbol de Archivos Actual

```
/app/
├── 📄 DOCUMENTACION_COMPLETA.md         # Documentación principal del proyecto
├── 📄 GUIA_DESARROLLO_CONTINUADO.md     # Guía para continuar desarrollo
├── 📄 ESTRUCTURA_COMPLETA_PROYECTO.md   # Este archivo - mapa completo
├── 📄 test_result.md                    # Estado de testing y comunicación
├── 📄 README.md                         # Descripción básica del proyecto
│
├── 🗂️ backend/                          # Backend FastAPI
│   ├── 📄 server.py                     # Aplicación principal FastAPI (1,000+ líneas)
│   ├── 📄 .env                          # Variables de entorno backend
│   └── 📄 requirements.txt              # Dependencias Python
│
├── 🗂️ frontend/                         # Frontend React
│   ├── 🗂️ src/
│   │   ├── 📄 App.js                    # Aplicación React principal (870+ líneas)
│   │   ├── 📄 App.css                   # Estilos personalizados
│   │   ├── 📄 index.js                  # Entry point React
│   │   ├── 📄 index.css                 # Estilos globales
│   │   ├── 🗂️ components/               # Componentes UI
│   │   │   └── 🗂️ ui/                   # shadcn/ui components
│   │   │       ├── 📄 button.jsx
│   │   │       ├── 📄 card.jsx
│   │   │       ├── 📄 input.jsx
│   │   │       ├── 📄 label.jsx
│   │   │       ├── 📄 tabs.jsx
│   │   │       ├── 📄 progress.jsx
│   │   │       ├── 📄 badge.jsx
│   │   │       ├── 📄 separator.jsx
│   │   │       └── 📄 toaster.jsx
│   │   ├── 🗂️ hooks/                    # Hooks personalizados
│   │   │   └── 📄 use-toast.js
│   │   └── 🗂️ lib/                      # Utilidades
│   │       └── 📄 utils.js
│   ├── 📄 .env                          # Variables de entorno frontend
│   ├── 📄 package.json                  # Dependencias Node.js
│   ├── 📄 tailwind.config.js           # Configuración Tailwind
│   └── 📄 components.json               # Configuración shadcn/ui
│
├── 🗂️ scripts/                         # Scripts de utilidad (si existen)
├── 🗂️ tests/                           # Tests automatizados (si existen)
└── 🗂️ uploads/                         # Directorio para archivos subidos (crear si no existe)
```

---

## 📋 Detalles de Archivos Clave

### 🔧 Backend (FastAPI)

#### `/app/backend/server.py` (1,000+ líneas)
```python
# Contenido principal:
- Configuración FastAPI con CORS
- Modelos Pydantic (User, Module, Progress, etc.)
- Autenticación JWT con bcrypt
- 12+ endpoints API completamente funcionales
- Conexión MongoDB con Motor AsyncIO
- 6 módulos ISTQB completos con contenido
- Sistema de progreso por secciones
- Logging y manejo de errores

# Endpoints implementados:
POST /api/auth/register
POST /api/auth/login  
GET  /api/auth/me
GET  /api/modules
GET  /api/modules/{module_id}
POST /api/modules
GET  /api/progress
POST /api/progress/{module_id}
POST /api/progress/{module_id}/section/{section_id}
GET  /api/dashboard/stats
```

#### `/app/backend/.env`
```env
MONGO_URL="mongodb://localhost:27017"
DB_NAME="istqb_platform"
CORS_ORIGINS="*"
JWT_SECRET_KEY="your-super-secret-jwt-key-change-in-production-istqb-2024"
```

#### `/app/backend/requirements.txt`
```txt
fastapi
motor
python-dotenv
pydantic[email]
python-jose[cryptography]
passlib[bcrypt]
uvicorn
bcrypt
```

---

### 🎨 Frontend (React)

#### `/app/frontend/src/App.js` (870+ líneas)
```javascript
// Componentes principales:
- AuthProvider (Context de autenticación)
- AuthPage (Login/Register)
- Dashboard (Página principal con estadísticas)
- StudyModule (Vista de estudio con navegación por secciones)
- ProtectedRoute (HOC para rutas protegidas)

// Funcionalidades:
- Sistema de autenticación completo
- Dashboard con métricas visuales
- Vista de estudio con progreso
- Navegación entre secciones
- Integración con API backend
- Manejo de errores y loading states
```

#### `/app/frontend/.env`
```env
REACT_APP_BACKEND_URL=https://testcert-hub-1.preview.emergentagent.com
WDS_SOCKET_PORT=443
```

#### `/app/frontend/package.json`
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-router-dom": "^6.8.1",
    "axios": "^1.3.4",
    "lucide-react": "^0.315.0",
    "@radix-ui/react-*": "^1.0.0"
  }
}
```

---

### 📊 Base de Datos (MongoDB)

#### Colecciones Existentes:
```javascript
// users - Información de usuarios
{
  _id: ObjectId,
  id: "uuid4",
  email: "user@email.com",
  full_name: "Nombre Completo",
  hashed_password: "bcrypt_hash",
  is_active: true,
  created_at: ISODate,
  study_progress: {},
  total_score: 0,
  modules_completed: 0
}

// istqb_modules - 6 módulos con contenido completo
{
  _id: ObjectId,
  id: "uuid4",
  title: "1. Fundamentos de las Pruebas",
  description: "Introducción a conceptos básicos...",
  content: "Contenido general del módulo",
  sections: [
    {
      id: "uuid4",
      title: "1.1 ¿Qué es el Testing?",
      content: "Contenido HTML detallado",
      order: 1
    }
  ],
  order: 1,
  estimated_time: 45,
  learning_objectives: ["Objetivo 1", "Objetivo 2"],
  key_concepts: ["Concepto 1", "Concepto 2"],
  created_at: ISODate
}

// user_progress - Progreso individual por módulo
{
  _id: ObjectId,
  id: "uuid4",
  user_id: "user_uuid",
  module_id: "module_uuid",
  completed: false,
  progress_percentage: 33,
  time_spent: 15,
  sections_completed: ["section_id_1"],
  last_accessed: ISODate,
  last_section_accessed: "section_id_1"
}
```

---

## 🚀 Estados de Servicios

### Supervisor Configuration
```ini
# Servicios corriendo:
[program:backend]
command=uvicorn server:app --host 0.0.0.0 --port 8001
directory=/app/backend
autostart=true
autorestart=true

[program:frontend]  
command=yarn start
directory=/app/frontend
autostart=true
autorestart=true

[program:mongodb]
command=mongod --dbpath /var/lib/mongodb
autostart=true
autorestart=true
```

### Puertos y URLs
- **Frontend**: Puerto 3000 (interno)
- **Backend**: Puerto 8001 (interno) con prefix `/api`
- **MongoDB**: Puerto 27017 (interno)
- **Acceso externo**: Via REACT_APP_BACKEND_URL

---

## 📈 Contenido Educativo Actual

### 6 Módulos ISTQB Foundation Level (285 min total)

#### 1. Fundamentos de las Pruebas (45 min)
```
├── 1.1 ¿Qué es el Testing?
├── 1.2 Los Siete Principios del Testing  
└── 1.3 Proceso Fundamental de Testing
```

#### 2. Testing a lo largo del Ciclo de Vida (50 min)
```
├── 2.1 Modelos de Ciclo de Vida del Software
└── 2.2 Niveles de Testing
```

#### 3. Técnicas de Testing Estático (40 min)
```
├── 3.1 Fundamentos del Testing Estático
└── 3.2 Proceso de Revisión
```

#### 4. Técnicas de Diseño de Pruebas (60 min)
```
├── 4.1 Técnicas de Caja Negra
└── 4.2 Técnicas de Caja Blanca
```

#### 5. Gestión de las Pruebas (55 min)
```
├── 5.1 Organización del Testing
└── 5.2 Planificación y Estimación
```

#### 6. Herramientas para el Testing (35 min)
```
├── 6.1 Clasificación de Herramientas
└── 6.2 Beneficios y Riesgos de la Automatización
```

---

## 🔧 Configuraciones Técnicas

### Tailwind CSS Config
```javascript
// tailwind.config.js
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Colores personalizados para la plataforma
      }
    }
  },
  plugins: []
}
```

### shadcn/ui Components
```
components/ui/
├── button.jsx      # Botones con variantes
├── card.jsx        # Cards para contenido
├── input.jsx       # Inputs de formulario
├── label.jsx       # Labels para formularios
├── tabs.jsx        # Pestañas de navegación
├── progress.jsx    # Barras de progreso
├── badge.jsx       # Badges para estados
├── separator.jsx   # Separadores visuales
└── toaster.jsx     # Sistema de notificaciones
```

---

## 🧪 Estado del Testing

### Backend Testing (100% Completado)
```yaml
✅ Autenticación (registro, login, token validation)
✅ Módulos ISTQB (obtener, crear, detalle)
✅ Sistema de progreso (actualizar, marcar secciones)
✅ Dashboard (estadísticas, métricas)
✅ Manejo de errores y validación
✅ Conexión MongoDB
```

### Frontend Testing (Pendiente)
```yaml
⚠️  Navegación entre rutas
⚠️  Formularios de auth
⚠️  Componentes de estudio
⚠️  Sistema de progreso visual
⚠️  Integración con API
```

---

## 📝 Archivos de Documentación

### `/app/test_result.md`
- Estado actual de testing
- Comunicación entre agentes
- Historial de cambios y fixes
- Lista de tareas completadas/pendientes

### `/app/DOCUMENTACION_COMPLETA.md`
- Documentación técnica completa
- Guías de API y modelos
- Información de deployment
- Recursos y enlaces útiles

### `/app/GUIA_DESARROLLO_CONTINUADO.md`
- Plan paso a paso para nuevas features
- Código de ejemplo para implementar
- Troubleshooting y debugging
- Roadmap de funcionalidades

---

## 🎯 Próximos Directorios a Crear

### Para Funcionalidades Futuras
```
/app/
├── uploads/                    # Para documentos PDF subidos
├── logs/                       # Logs de aplicación (opcional)
├── scripts/                    # Scripts de utilidad
│   ├── migrate.py             # Migraciones de BD
│   ├── seed.py                # Datos de prueba
│   └── backup.py              # Backup de datos
├── tests/                      # Tests automatizados
│   ├── backend/               # Tests de API
│   └── frontend/              # Tests de componentes
└── docs/                      # Documentación adicional
    ├── api.md                 # Documentación de API
    └── deployment.md          # Guía de deployment
```

---

## 💾 Comandos de Respaldo

### Backup Completo del Proyecto
```bash
# Crear backup del código
tar -czf istqb_backup_$(date +%Y%m%d).tar.gz /app

# Backup de MongoDB
mongodump --db istqb_platform --out /app/backup/

# Backup solo de la configuración
cp /app/backend/.env /app/backup/backend_env
cp /app/frontend/.env /app/backup/frontend_env
```

### Restaurar Proyecto
```bash
# Restaurar código
tar -xzf istqb_backup_YYYYMMDD.tar.gz

# Restaurar MongoDB
mongorestore --db istqb_platform /app/backup/istqb_platform/

# Reinstalar dependencias
cd /app/backend && pip install -r requirements.txt
cd /app/frontend && yarn install
```

---

## 🔍 Investigar/Verificar

### Si Algo No Funciona
1. **Verificar servicios**: `sudo supervisorctl status`
2. **Ver logs**: `tail -f /var/log/supervisor/*.log`
3. **Verificar puertos**: `netstat -tlnp | grep :3000`
4. **MongoDB**: `mongo istqb_platform --eval "db.stats()"`
5. **Variables de entorno**: `cat /app/backend/.env`

---

**📊 Estado del Proyecto: MVP FUNCIONAL**
- ✅ Backend completo y probado
- ✅ Frontend funcional con UI moderna  
- ✅ 6 módulos ISTQB con contenido detallado
- ✅ Sistema de progreso implementado
- ✅ Autenticación JWT funcionando
- 🔄 Listo para expansión de funcionalidades

*Última actualización: Durante desarrollo activo*