import React, { useState, useEffect, createContext, useContext } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';
import './App.css';

// Components
import { Button } from './components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Progress } from './components/ui/progress';
import { Badge } from './components/ui/badge';
import { Separator } from './components/ui/separator';
import { useToast } from './hooks/use-toast';
import { Toaster } from './components/ui/toaster';
import { BookOpen, Clock, Award, TrendingUp, User, LogOut, Home, FileText, ChevronLeft, ChevronRight, CheckCircle, ArrowLeft } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext();

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUser();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchUser = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
    } catch (error) {
      console.error('Error fetching user:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      const { access_token, user: userData } = response.data;
      
      localStorage.setItem('token', access_token);
      setToken(access_token);
      setUser(userData);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Error al iniciar sesión' 
      };
    }
  };

  const register = async (email, password, fullName) => {
    try {
      const response = await axios.post(`${API}/auth/register`, {
        email,
        password,
        full_name: fullName
      });
      const { access_token, user: userData } = response.data;
      
      localStorage.setItem('token', access_token);
      setToken(access_token);
      setUser(userData);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Error al registrarse' 
      };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    delete axios.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{ 
      user, 
      token, 
      loading, 
      login, 
      register, 
      logout,
      isAuthenticated: !!user 
    }}>
      {children}
    </AuthContext.Provider>
  );
};

// Auth Components
const AuthPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { login, register } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      let result;
      if (isLogin) {
        result = await login(email, password);
      } else {
        result = await register(email, password, fullName);
      }

      if (result.success) {
        toast({
          title: isLogin ? "¡Bienvenido!" : "¡Cuenta creada!",
          description: isLogin ? "Has iniciado sesión correctamente" : "Tu cuenta ha sido creada exitosamente",
        });
        // Force navigation after successful auth
        setTimeout(() => {
          navigate('/', { replace: true });
        }, 100);
      } else {
        toast({
          title: "Error",
          description: result.error,
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Ha ocurrido un error inesperado",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="mx-auto h-20 w-20 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl flex items-center justify-center mb-4">
            <BookOpen className="h-10 w-10 text-white" />
          </div>
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            ISTQB Study Platform
          </h2>
          <p className="text-gray-600">
            Tu plataforma de preparación para la certificación ISTQB
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>{isLogin ? 'Iniciar Sesión' : 'Crear Cuenta'}</CardTitle>
            <CardDescription>
              {isLogin 
                ? 'Ingresa tus credenciales para acceder' 
                : 'Completa los datos para crear tu cuenta'
              }
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {!isLogin && (
                <div>
                  <Label htmlFor="fullName">Nombre Completo</Label>
                  <Input
                    id="fullName"
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    required
                    placeholder="Ingresa tu nombre completo"
                  />
                </div>
              )}
              
              <div>
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  placeholder="tu@email.com"
                />
              </div>
              
              <div>
                <Label htmlFor="password">Contraseña</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  placeholder="••••••••"
                />
              </div>
              
              <Button 
                type="submit" 
                className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700" 
                disabled={loading}
              >
                {loading ? 'Procesando...' : (isLogin ? 'Iniciar Sesión' : 'Crear Cuenta')}
              </Button>
            </form>
            
            <div className="mt-4 text-center">
              <Button
                variant="link"
                onClick={() => setIsLogin(!isLogin)}
                className="text-blue-600 hover:text-blue-800"
              >
                {isLogin 
                  ? '¿No tienes cuenta? Regístrate' 
                  : '¿Ya tienes cuenta? Inicia sesión'
                }
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// Study Module Component
const StudyModule = () => {
  const { moduleId } = useParams();
  const [module, setModule] = useState(null);
  const [progress, setProgress] = useState(null);
  const [currentSection, setCurrentSection] = useState(0);
  const [loading, setLoading] = useState(true);
  const [startTime] = useState(Date.now());
  
  const { user } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();

  useEffect(() => {
    fetchModuleData();
  }, [moduleId]);

  const fetchModuleData = async () => {
    try {
      const [moduleRes, progressRes] = await Promise.all([
        axios.get(`${API}/modules/${moduleId}`),
        axios.get(`${API}/progress`)
      ]);
      
      setModule(moduleRes.data);
      const moduleProgress = progressRes.data.find(p => p.module_id === moduleId);
      setProgress(moduleProgress || { sections_completed: [], progress_percentage: 0 });
    } catch (error) {
      toast({
        title: "Error",
        description: "No se pudo cargar el módulo",
        variant: "destructive",
      });
      navigate('/');
    } finally {
      setLoading(false);
    }
  };

  const markSectionComplete = async (sectionId) => {
    try {
      const response = await axios.post(`${API}/progress/${moduleId}/section/${sectionId}`);
      
      // Update local progress
      setProgress(prev => ({
        ...prev,
        sections_completed: [...(prev.sections_completed || []), sectionId],
        progress_percentage: response.data.progress_percentage
      }));

      toast({
        title: "¡Sección completada!",
        description: `Progreso: ${response.data.progress_percentage}%`,
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "No se pudo marcar la sección como completada",
        variant: "destructive",
      });
    }
  };

  const updateTimeSpent = async () => {
    const timeSpent = Math.floor((Date.now() - startTime) / 60000); // Convert to minutes
    if (timeSpent > 0) {
      try {
        await axios.post(`${API}/progress/${moduleId}?progress_percentage=${progress?.progress_percentage || 0}&time_spent=${timeSpent}`);
      } catch (error) {
        console.error('Error updating time spent:', error);
      }
    }
  };

  // Update time spent when component unmounts
  useEffect(() => {
    return () => {
      updateTimeSpent();
    };
  }, []);

  const nextSection = () => {
    if (currentSection < module.sections.length - 1) {
      setCurrentSection(currentSection + 1);
    }
  };

  const prevSection = () => {
    if (currentSection > 0) {
      setCurrentSection(currentSection - 1);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p>Cargando módulo...</p>
        </div>
      </div>
    );
  }

  if (!module) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p>Módulo no encontrado</p>
          <Button onClick={() => navigate('/')} className="mt-4">
            Volver al Dashboard
          </Button>
        </div>
      </div>
    );
  }

  const currentSectionData = module.sections[currentSection];
  const isSectionCompleted = progress?.sections_completed?.includes(currentSectionData.id);
  const completedSections = progress?.sections_completed?.length || 0;
  const totalSections = module.sections.length;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <Button 
                variant="ghost" 
                onClick={() => navigate('/')}
                className="mr-4"
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Dashboard
              </Button>
              <div className="h-10 w-10 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center mr-3">
                <BookOpen className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">{module.title}</h1>
                <p className="text-sm text-gray-600">
                  Sección {currentSection + 1} de {totalSections} • {completedSections}/{totalSections} completadas
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">{user?.full_name}</p>
                <p className="text-xs text-gray-500">Progreso: {progress?.progress_percentage || 0}%</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar - Progress & Navigation */}
          <div className="lg:col-span-1">
            <Card className="sticky top-8">
              <CardHeader>
                <CardTitle className="text-lg">Progreso del Módulo</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span>Completado</span>
                      <span>{progress?.progress_percentage || 0}%</span>
                    </div>
                    <Progress value={progress?.progress_percentage || 0} className="h-2" />
                  </div>
                  
                  <Separator />
                  
                  <div>
                    <h4 className="font-semibold mb-3">Secciones</h4>
                    <div className="space-y-2">
                      {module.sections.map((section, index) => {
                        const isCompleted = progress?.sections_completed?.includes(section.id);
                        const isCurrent = index === currentSection;
                        
                        return (
                          <div
                            key={section.id}
                            className={`flex items-center p-2 rounded-lg cursor-pointer transition-colors ${
                              isCurrent 
                                ? 'bg-blue-100 border border-blue-300' 
                                : 'hover:bg-gray-100'
                            }`}
                            onClick={() => setCurrentSection(index)}
                          >
                            <div className="mr-3">
                              {isCompleted ? (
                                <CheckCircle className="h-5 w-5 text-green-600" />
                              ) : (
                                <div className={`h-5 w-5 rounded-full border-2 ${
                                  isCurrent ? 'border-blue-600' : 'border-gray-300'
                                }`} />
                              )}
                            </div>
                            <div className="flex-1">
                              <p className={`text-sm font-medium ${
                                isCurrent ? 'text-blue-900' : 'text-gray-900'
                              }`}>
                                {section.title}
                              </p>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                  
                  <Separator />
                  
                  <div className="space-y-2">
                    <div className="flex items-center text-sm text-gray-600">
                      <Clock className="h-4 w-4 mr-2" />
                      <span>{module.estimated_time} min estimados</span>
                    </div>
                    <div className="flex items-center text-sm text-gray-600">
                      <Award className="h-4 w-4 mr-2" />
                      <span>{module.learning_objectives?.length || 0} objetivos</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3">
            <Card>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-2xl">{currentSectionData.title}</CardTitle>
                    <CardDescription className="mt-2">
                      Sección {currentSection + 1} de {totalSections}
                    </CardDescription>
                  </div>
                  {!isSectionCompleted && (
                    <Button
                      onClick={() => markSectionComplete(currentSectionData.id)}
                      variant="outline"
                      size="sm"
                    >
                      <CheckCircle className="h-4 w-4 mr-2" />
                      Marcar Completada
                    </Button>
                  )}
                  {isSectionCompleted && (
                    <Badge variant="secondary" className="bg-green-100 text-green-800">
                      <CheckCircle className="h-4 w-4 mr-1" />
                      Completada
                    </Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="prose prose-lg max-w-none">
                  <div 
                    className="content-area"
                    dangerouslySetInnerHTML={{ 
                      __html: currentSectionData.content.replace(/\n/g, '<br>').replace(/## /g, '<h2>').replace(/### /g, '<h3>').replace(/# /g, '<h1>') 
                    }} 
                  />
                </div>
                
                {/* Navigation */}
                <div className="flex justify-between items-center mt-8 pt-6 border-t">
                  <Button
                    variant="outline"
                    onClick={prevSection}
                    disabled={currentSection === 0}
                  >
                    <ChevronLeft className="h-4 w-4 mr-2" />
                    Anterior
                  </Button>
                  
                  <span className="text-sm text-gray-500">
                    {currentSection + 1} de {totalSections}
                  </span>
                  
                  {currentSection < totalSections - 1 ? (
                    <Button onClick={nextSection}>
                      Siguiente
                      <ChevronRight className="h-4 w-4 ml-2" />
                    </Button>
                  ) : (
                    <Button 
                      onClick={() => navigate('/')}
                      className="bg-green-600 hover:bg-green-700"
                    >
                      Completar Módulo
                      <CheckCircle className="h-4 w-4 ml-2" />
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
            
            {/* Module Info */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
              <Card>
                <CardHeader>
                  <CardTitle>Objetivos de Aprendizaje</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {module.learning_objectives?.map((objective, index) => (
                      <li key={index} className="flex items-start">
                        <div className="h-2 w-2 bg-blue-600 rounded-full mt-2 mr-3 flex-shrink-0" />
                        <span className="text-sm text-gray-700">{objective}</span>
                      </li>
                    )) || <li>No hay objetivos definidos</li>}
                  </ul>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader>
                  <CardTitle>Conceptos Clave</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {module.key_concepts?.map((concept, index) => (
                      <Badge key={index} variant="secondary">
                        {concept}
                      </Badge>
                    )) || <span className="text-sm text-gray-500">No hay conceptos definidos</span>}
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [modules, setModules] = useState([]);
  const [progress, setProgress] = useState([]);
  const { user, logout } = useAuth();
  const { toast } = useToast();

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [statsRes, modulesRes, progressRes] = await Promise.all([
        axios.get(`${API}/dashboard/stats`),
        axios.get(`${API}/modules`),
        axios.get(`${API}/progress`)
      ]);
      
      setStats(statsRes.data);
      setModules(modulesRes.data);
      setProgress(progressRes.data);
    } catch (error) {
      toast({
        title: "Error",
        description: "No se pudieron cargar los datos del dashboard",
        variant: "destructive",
      });
    }
  };

  if (!stats) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p>Cargando dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <div className="h-10 w-10 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center mr-3">
                <BookOpen className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">ISTQB Study Platform</h1>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">{user?.full_name}</p>
                <p className="text-xs text-gray-500">{user?.email}</p>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={logout}
                className="flex items-center"
              >
                <LogOut className="h-4 w-4 mr-2" />
                Salir
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            ¡Hola, {user?.full_name?.split(' ')[0]}!
          </h2>
          <p className="text-gray-600">
            Continúa tu preparación para la certificación ISTQB Foundation Level
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardContent className="flex items-center p-6">
              <div className="p-2 bg-blue-100 rounded-lg mr-4">
                <BookOpen className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">{stats.completed_modules}</p>
                <p className="text-sm text-gray-600">Módulos Completados</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="flex items-center p-6">
              <div className="p-2 bg-green-100 rounded-lg mr-4">
                <Award className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">{stats.completion_percentage}%</p>
                <p className="text-sm text-gray-600">Progreso Total</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="flex items-center p-6">
              <div className="p-2 bg-purple-100 rounded-lg mr-4">
                <Clock className="h-6 w-6 text-purple-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">{Math.floor(stats.total_time_spent / 60)}h {stats.total_time_spent % 60}m</p>
                <p className="text-sm text-gray-600">Tiempo de Estudio</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="flex items-center p-6">
              <div className="p-2 bg-orange-100 rounded-lg mr-4">
                <TrendingUp className="h-6 w-6 text-orange-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">{stats.total_modules}</p>
                <p className="text-sm text-gray-600">Total Módulos</p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Progress Overview */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Progreso General</CardTitle>
            <CardDescription>
              Tu avance en la preparación ISTQB Foundation Level
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span>Progreso del Curso</span>
                  <span>{stats.completion_percentage}%</span>
                </div>
                <Progress value={stats.completion_percentage} className="h-2" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Modules List */}
        <Card>
          <CardHeader>
            <CardTitle>Módulos de Estudio</CardTitle>
            <CardDescription>
              Contenido organizado del temario ISTQB Foundation Level
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {modules.map((module) => {
                const moduleProgress = progress.find(p => p.module_id === module.id);
                const isCompleted = moduleProgress?.completed || false;
                const progressPercentage = moduleProgress?.progress_percentage || 0;
                
                return (
                  <div key={module.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                    <div className="flex-1">
                      <div className="flex items-center mb-2">
                        <h3 className="font-semibold text-gray-900 mr-3">{module.title}</h3>
                        {isCompleted && (
                          <Badge variant="secondary" className="bg-green-100 text-green-800">
                            Completado
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 mb-2">{module.description}</p>
                      <div className="flex items-center text-xs text-gray-500">
                        <Clock className="h-3 w-3 mr-1" />
                        <span>{module.estimated_time} minutos</span>
                      </div>
                      {progressPercentage > 0 && (
                        <div className="mt-2">
                          <Progress value={progressPercentage} className="h-1" />
                        </div>
                      )}
                    </div>
                    <Button 
                      variant={isCompleted ? "secondary" : "default"}
                      className="ml-4"
                      onClick={() => navigate(`/study/${module.id}`)}
                    >
                      {isCompleted ? "Revisar" : "Estudiar"}
                    </Button>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p>Cargando...</p>
        </div>
      </div>
    );
  }
  
  return isAuthenticated ? children : <Navigate to="/auth" replace />;
};

// Main App Component
function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="App">
          <Routes>
            <Route path="/auth" element={<AuthPage />} />
            <Route path="/" element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
          <Toaster />
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;