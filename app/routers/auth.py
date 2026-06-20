from fastapi import APIRouter, Depends, Request, Form, Response, status
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session
from app.database.database import get_session
from app.models.models import Usuario
from app.services.auth import (
    hash_password, 
    verify_password, 
    create_access_token, 
    get_current_user_optional
)

router = APIRouter(prefix="/auth", tags=["AUTENTICACIÓN"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, current_user: Usuario = Depends(get_current_user_optional)):
    """Renderiza la página de inicio de sesión. Si el usuario ya está logueado, lo redirige."""
    if current_user:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@router.post("/login")
async def login(
    request: Request,
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_session)
):
    """Procesa las credenciales de inicio de sesión e inyecta la cookie de sesión."""
    # Buscar usuario
    user = db.query(Usuario).filter(Usuario.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            "login.html", 
            {"request": request, "error": "Correo electrónico o contraseña incorrectos."}
        )
    
    # Crear token
    token = create_access_token(data={"sub": user.email})
    
    # Redirigir al inicio e inyectar cookie HTTPOnly
    redirect_response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    # Expiración en 7 días para coincidir con settings.SESSION_MAX_AGE
    redirect_response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        max_age=60 * 60 * 24 * 7,
        samesite="lax",
        secure=False  # Cambiar a True en producción con HTTPS
    )
    return redirect_response

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, current_user: Usuario = Depends(get_current_user_optional)):
    """Renderiza la página de registro de usuarios."""
    if current_user:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("registro.html", {"request": request, "error": None})

@router.post("/register")
async def register(
    request: Request,
    nombre: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    telefono: str = Form(None),
    direccion: str = Form(None),
    ciudad: str = Form(None),
    departamento: str = Form(None),
    db: Session = Depends(get_session)
):
    """Crea una nueva cuenta de usuario, hashea la contraseña y redirige al inicio de sesión."""
    # Verificar si el email ya existe
    existing_user = db.query(Usuario).filter(Usuario.email == email).first()
    if existing_user:
        return templates.TemplateResponse(
            "registro.html", 
            {"request": request, "error": "El correo electrónico ya está registrado."}
        )
    
    # Hashear contraseña y crear usuario
    hashed = hash_password(password)
    nuevo_usuario = Usuario(
        nombre=nombre,
        email=email,
        hashed_password=hashed,
        telefono=telefono,
        direccion=direccion,
        ciudad=ciudad,
        departamento=departamento,
        rol="cliente"  # Rol cliente por defecto
    )
    
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    
    # Redirigir al login con un parámetro de éxito (o iniciar sesión automáticamente)
    # Por simplicidad e inmediatez del UX, iniciaremos sesión automáticamente
    token = create_access_token(data={"sub": nuevo_usuario.email})
    redirect_response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    redirect_response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        max_age=60 * 60 * 24 * 7,
        samesite="lax",
        secure=False
    )
    return redirect_response

@router.get("/logout")
async def logout():
    """Borra la cookie de sesión del navegador y redirige a la página principal."""
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="access_token")
    return response
