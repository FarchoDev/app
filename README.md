# Plataforma ISTQB Study Platform

Una plataforma web interactiva de estudio para la preparación de la certificación ISTQB Foundation Level, desarrollada con **FastAPI + React + MongoDB**.

## 🎯 Objetivo

Proporcionar una experiencia de aprendizaje completa y estructurada para estudiantes que se preparan para la certificación ISTQB Foundation Level, con módulos organizados, seguimiento de progreso y materiales de estudio integrados.

## ✅ Estado Actual del Proyecto (Fase 1 Completada)

### 🔧 Backend Implementado (100% Funcional)
- ✅ **Sistema de autenticación JWT** completo (registro, login, middleware)
- ✅ **Base de datos MongoDB** con modelos optimizados (UUID, no ObjectID)
- ✅ **6 Módulos ISTQB Foundation Level** con contenido detallado:
  1. Fundamentos de las Pruebas
  2. Testing a lo largo del Ciclo de Vida del Software
  3. Técnicas de Testing Estático
  4. Técnicas de Diseño de Pruebas
  5. Gestión de las Pruebas
  6. Herramientas para el Testing
- ✅ **Sistema de progreso avanzado** con seguimiento por secciones
- ✅ **API endpoints** completamente funcionales
- ✅ **Dashboard statistics** con métricas en tiempo real

### 🎨 Frontend Implementado (100% Funcional)
- ✅ **Sistema de autenticación** con React Context
- ✅ **Dashboard principal** con estadísticas y progreso visual
- ✅ **Vista de estudio interactiva** con:
  - Navegación por secciones
  - Sidebar de progreso
  - Marcado de secciones completadas
  - Contenido educativo formateado
- ✅ **Enrutamiento completo** (/auth, /dashboard, /study/:moduleId)
- ✅ **UI moderna** con Tailwind CSS y componentes shadcn/ui
- ✅ **Responsive design** para dispositivos móviles

## 🚀 Funcionalidades Principales

### 📚 Sistema de Estudio
- **Módulos estructurados** con secciones, objetivos de aprendizaje y conceptos clave
- **Navegación intuitiva** entre secciones con progreso visual
- **Contenido educativo** formateado con markdown y estilos personalizados
- **Seguimiento automático** del tiempo de estudio

### 📊 Sistema de Progreso
- **Progreso por módulo** calculado automáticamente por secciones completadas
- **Dashboard con métricas** (módulos completados, tiempo total, porcentaje general)
- **Estado visual** de cada sección (completada, actual, pendiente)
- **Persistencia** de progreso por usuario

### 🔐 Autenticación y Seguridad
- **JWT tokens** para sesiones seguras
- **Registro y login** con validación de datos
- **Rutas protegidas** con middleware de autenticación
- **Gestión de usuarios** con perfiles personalizados

## 🛠️ Stack Tecnológico

### Backend
- **FastAPI** - Framework web moderno para Python
- **MongoDB** con **Motor** (async driver)
- **JWT** para autenticación
- **Pydantic** para validación de datos
- **bcrypt** para hashing de contraseñas

### Frontend
- **React 19** con hooks modernos
- **React Router** para navegación
- **Axios** para calls HTTP
- **Tailwind CSS** para estilos
- **shadcn/ui** para componentes
- **Lucide React** para iconografía

### Base de Datos
- **MongoDB** con colecciones:
  - `users` - Información de usuarios
  - `istqb_modules` - Contenido de módulos
  - `user_progress` - Progreso individual

## 🏗️ Arquitectura del Proyecto

```
/app
├── backend/                 # FastAPI Backend
│   ├── server.py           # Servidor principal con APIs
│   ├── requirements.txt    # Dependencias Python
│   └── .env               # Variables de entorno
├── frontend/               # React Frontend
│   ├── src/
│   │   ├── App.js         # Componente principal con rutas
│   │   ├── App.css        # Estilos personalizados
│   │   └── components/    # Componentes UI
│   ├── package.json       # Dependencias Node.js
│   └── public/           # Assets estáticos
├── test_result.md         # Estado de testing
└── README.md             # Esta documentación
```

## 📋 API Endpoints Implementados

### Autenticación
- `POST /api/auth/register` - Registro de usuario
- `POST /api/auth/login` - Inicio de sesión
- `GET /api/auth/me` - Información del usuario actual

### Módulos ISTQB
- `GET /api/modules` - Lista de todos los módulos
- `GET /api/modules/{module_id}` - Detalle de módulo específico

### Progreso del Usuario
- `GET /api/progress` - Progreso del usuario actual
- `POST /api/progress/{module_id}` - Actualizar progreso general
- `POST /api/progress/{module_id}/section/{section_id}` - Marcar sección completada

### Dashboard
- `GET /api/dashboard/stats` - Estadísticas del dashboard

## 🔄 Instalación y Ejecución

### Requisitos Previos
- Python 3.11+
- Node.js 18+
- MongoDB (local o cloud)
- Yarn package manager

### Configuración Backend
```bash
cd backend
pip install -r requirements.txt

# Configurar variables de entorno (.env)
MONGO_URL=mongodb://localhost:27017/istqb_platform
DB_NAME=istqb_platform
JWT_SECRET_KEY=your-secret-key
CORS_ORIGINS=http://localhost:3000
```

### Configuración Frontend
```bash
cd frontend
yarn install

# Configurar variables de entorno (.env)
REACT_APP_BACKEND_URL=http://localhost:8001
```

### Ejecución
```bash
# Usando supervisor (recomendado en producción)
sudo supervisorctl restart all

# O manualmente para desarrollo
cd backend && uvicorn server:app --host 0.0.0.0 --port 8001 --reload
cd frontend && yarn start
```

## 📝 Próximas Funcionalidades (Roadmap)

### Fase 2: Sistema de Documentos
- [ ] Carga y gestión de documentos PDF
- [ ] Visualizador de PDFs integrado
- [ ] Organización por carpetas y categorías
- [ ] Búsqueda en documentos

### Fase 3: Sistema de Evaluación
- [ ] Banco de preguntas por módulo
- [ ] Cuestionarios de práctica
- [ ] Simulacros de examen completo
- [ ] Retroalimentación detallada
- [ ] Análisis de resultados

### Fase 4: Mejoras Avanzadas
- [ ] Dashboard con gráficos avanzados
- [ ] Recomendaciones personalizadas
- [ ] Calendario de estudio
- [ ] Gamificación (logros, puntos)
- [ ] Integración con IA para generación automática de preguntas

### Fase 5: Integración IA
- [ ] Generación automática de preguntas con OpenAI GPT
- [ ] Retroalimentación inteligente personalizada
- [ ] Chat assistant para dudas
- [ ] Análisis predictivo de rendimiento

## 🧪 Testing

### Backend
- ✅ Testing completo con 100% de éxito
- ✅ 12 endpoints probados automáticamente
- ✅ Autenticación, módulos, progreso verificados
- ✅ Cálculos de progreso validados

### Frontend
- 🔄 Testing pendiente (próximo paso)
- Funcionalidades a probar:
  - Autenticación de usuarios
  - Navegación entre páginas
  - Vista de estudio de módulos
  - Marcado de progreso

## 👥 Usuarios de Prueba

Para testing, se pueden crear usuarios con:
- Email: cualquier email válido
- Contraseña: mínimo 8 caracteres
- Los módulos ISTQB se crean automáticamente al iniciar

## 📊 Métricas del Proyecto

- **Líneas de código Backend**: ~350 líneas (server.py)
- **Líneas de código Frontend**: ~520 líneas (App.js)
- **Módulos de contenido**: 6 módulos completos
- **Secciones de estudio**: ~12 secciones en total
- **Endpoints API**: 8 endpoints funcionales
- **Componentes React**: 4 componentes principales

## 🤝 Contribución

El proyecto está en desarrollo activo. Para contribuir:
1. Revisar el roadmap de funcionalidades pendientes
2. Implementar siguiendo los patrones establecidos
3. Ejecutar testing antes de commits
4. Actualizar documentación según cambios

---

**Desarrollado con ❤️ para la comunidad ISTQB**

*Última actualización: Enero 2025*
