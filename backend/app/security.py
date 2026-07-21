from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from passlib.context import CryptContext
from fastapi import Request, HTTPException, status

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_serializer = URLSafeTimedSerializer(settings.SECRET_KEY, salt="bgeigie-session")


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


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
            headers={"Location": "/login"},
        )
    return username
