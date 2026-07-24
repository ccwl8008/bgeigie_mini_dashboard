from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import HTTPException as FastAPIHTTPException
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.database import Base, engine, SessionLocal
from app.models import Usuario
from app.security import hash_password
from app.config import settings
from app.routers import ingest, auth, dashboard, admin

app = FastAPI(title="bGeigie Dashboard")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(ingest.router)
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(admin.router)


@app.exception_handler(FastAPIHTTPException)
async def redirect_on_auth_error(request: Request, exc: FastAPIHTTPException):
    """Si la dependencia de sesión lanza 303 con Location, lo respetamos
    como una redirección de verdad al login en vez de un JSON de error."""
    location = exc.headers.get("Location") if exc.headers else None
    if location:
        return RedirectResponse(url=location, status_code=exc.status_code)
    raise exc


def _migrar_columna_es_admin(db):
    """Agrega la columna es_admin a instalaciones que ya tenian la tabla
    Usuario creada antes de que existiera este rol (evita tener que
    correr un ALTER TABLE a mano en la base de datos ya desplegada)."""
    try:
        db.execute(text("ALTER TABLE Usuario ADD COLUMN es_admin TINYINT(1) DEFAULT 0"))
        db.commit()
    except OperationalError:
        # ya existe la columna (instalacion nueva, o migracion ya corrida antes)
        db.rollback()


@app.on_event("startup")
def on_startup():
    # Crea las tablas si no existen (no pisa nada si ya vinieron de la
    # migración/backup restaurado).
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        _migrar_columna_es_admin(db)

        existe = db.query(Usuario).filter(Usuario.username == settings.ADMIN_USERNAME).first()
        if not existe and settings.ADMIN_PASSWORD:
            admin_user = Usuario(
                username=settings.ADMIN_USERNAME,
                password_hash=hash_password(settings.ADMIN_PASSWORD),
                nombre_completo=settings.ADMIN_NOMBRE,
                activo=1,
                es_admin=1,
            )
            db.add(admin_user)
            db.commit()
        elif existe and not existe.es_admin:
            # Si el usuario admin configurado ya existia (de un despliegue
            # previo a que existiera este rol), lo promovemos a admin.
            existe.es_admin = 1
            db.commit()
    finally:
        db.close()
