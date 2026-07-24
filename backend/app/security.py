import hashlib

from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from passlib.context import CryptContext
from fastapi import Request, HTTPException, status, Depends

from app.config import settings
from app.database import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_serializer = URLSafeTimedSerializer(settings.SECRET_KEY, salt="bgeigie-session")


def _prehash(plain_password: str) -> str:
    """bcrypt solo admite hasta 72 bytes y las versiones recientes de la
    librería lanzan error en vez de truncar. Pre-hasheamos con SHA-256
    (siempre 64 caracteres hex, muy por debajo del límite) para que
    cualquier contraseña -larga, con emojis, lo que sea- funcione siempre."""
    return hashlib.sha256(plain_password.encode("utf-8")).hexdigest()


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(_prehash(plain_password))


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(_prehash(plain_password), password_hash)


def create_session_token(username: str) -> str:
    return _serializer.dumps({"username": username})


def read_session_token(token: str) -> str | None:
    try:
        data = _serializer.loads(token, max_age=settings.SESSION_MAX_AGE_SECONDS)
        return data.get("username")
    except (BadSignature, SignatureExpired):
        return None


def get_current_username(request: Request) -> str:
    """Dependency: exige una sesión válida o redirige/lanza 401.
    Las rutas de página usan esto para forzar el login."""
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    username = read_session_token(token) if token else None
    if not username:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": f"{settings.BASE_PATH}/login"},
        )
    return username


def require_admin(request: Request, db=Depends(get_db)):
    """Dependency: igual que get_current_username, pero ademas exige que
    el usuario tenga es_admin=1. Devuelve el objeto Usuario completo."""
    from app.models import Usuario  # import tardio para evitar ciclos

    username = get_current_username(request)
    usuario = db.query(Usuario).filter(Usuario.username == username).first()

    if not usuario or not usuario.es_admin:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": f"{settings.BASE_PATH}/"},
        )
    return usuario
