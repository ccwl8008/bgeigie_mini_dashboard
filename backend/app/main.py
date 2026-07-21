from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import HTTPException as FastAPIHTTPException

from app.database import Base, engine, SessionLocal
from app.models import Usuario
from app.security import hash_password
from app.config import settings
from app.routers import ingest, auth, dashboard

app = FastAPI(title="bGeigie Dashboard")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(ingest.router)
app.include_router(auth.router)
app.include_router(dashboard.router)


@app.exception_handler(FastAPIHTTPException)
async def redirect_on_auth_error(request: Request, exc: FastAPIHTTPException):
    """Si la dependencia de sesión lanza 303 con Location, lo respetamos
    como una redirección de verdad al login en vez de un JSON de error."""
    location = exc.headers.get("Location") if exc.headers else None
    if location:
        return RedirectResponse(url=location, status_code=exc.status_code)
    raise exc


@app.on_event("startup")
def on_startup():
    # Crea las tablas si no existen (no pisa nada si ya vinieron de la
    # migración/backup restaurado).
    Base.metadata.create_all(bind=engine)

    # Siembra el usuario admin inicial una sola vez.
    db = SessionLocal()
    try:
        existe = db.query(Usuario).filter(Usuario.username == settings.ADMIN_USERNAME).first()
        if not existe and settings.ADMIN_PASSWORD:
            admin = Usuario(
                username=settings.ADMIN_USERNAME,
                password_hash=hash_password(settings.ADMIN_PASSWORD),
                nombre_completo=settings.ADMIN_NOMBRE,
                activo=1,
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()
