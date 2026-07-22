from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Usuario
from app.security import verify_password, create_session_token
from app.config import settings
from app.templates_config import templates

router = APIRouter()
BP = settings.BASE_PATH  # atajo


@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request, error: str | None = None):
    return templates.TemplateResponse(
        "login.html", {"request": request, "error": error}
    )


@router.post("/login")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    usuario = db.query(Usuario).filter(Usuario.username == username, Usuario.activo == 1).first()

    if not usuario or not verify_password(password, usuario.password_hash):
        return RedirectResponse(
            url=f"{BP}/login?error=Usuario o contraseña incorrectos", status_code=303
        )

    token = create_session_token(usuario.username)
    response = RedirectResponse(url=f"{BP}/", status_code=303)
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=token,
        max_age=settings.SESSION_MAX_AGE_SECONDS,
        httponly=True,
        samesite="lax",
        path=BP or "/",
    )
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url=f"{BP}/login", status_code=303)
    response.delete_cookie(settings.SESSION_COOKIE_NAME, path=BP or "/")
    return response
