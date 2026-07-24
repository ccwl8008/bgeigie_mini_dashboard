import csv
import io

from fastapi import APIRouter, Depends, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models import Usuario, DataRadiacion
from app.security import require_admin, hash_password
from app.config import settings
from app.templates_config import templates

router = APIRouter()
BP = settings.BASE_PATH


@router.get("/admin", response_class=HTMLResponse)
async def admin_page(
    request: Request,
    admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    usuarios = db.query(Usuario).order_by(Usuario.id).all()
    sensores = [s[0] for s in db.query(DataRadiacion.SensorID).distinct().all() if s[0]]
    return templates.TemplateResponse(
        "admin.html",
        {"request": request, "usuarios": usuarios, "sensores": sensores, "admin": admin},
    )


@router.post("/admin/usuarios")
async def crear_usuario(
    username: str = Form(...),
    password: str = Form(...),
    nombre_completo: str = Form(""),
    es_admin: str = Form(None),  # llega "on" si el checkbox esta marcado
    admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    existe = db.query(Usuario).filter(Usuario.username == username).first()
    if existe:
        return RedirectResponse(url=f"{BP}/admin?error=El usuario ya existe", status_code=303)

    nuevo = Usuario(
        username=username,
        password_hash=hash_password(password),
        nombre_completo=nombre_completo,
        activo=1,
        es_admin=1 if es_admin else 0,
    )
    db.add(nuevo)
    db.commit()
    return RedirectResponse(url=f"{BP}/admin", status_code=303)


@router.post("/admin/usuarios/{usuario_id}/toggle")
async def alternar_usuario(
    usuario_id: int,
    admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if usuario and usuario.id != admin.id:  # no te puedes desactivar a ti mismo
        usuario.activo = 0 if usuario.activo else 1
        db.commit()
    return RedirectResponse(url=f"{BP}/admin", status_code=303)


@router.post("/admin/usuarios/{usuario_id}/eliminar")
async def eliminar_usuario(
    usuario_id: int,
    admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if usuario and usuario.id != admin.id:  # no te puedes eliminar a ti mismo
        db.delete(usuario)
        db.commit()
    return RedirectResponse(url=f"{BP}/admin", status_code=303)


@router.get("/api/exportar")
async def exportar_csv(
    sensor_id: str | None = Query(None, alias="sensorID"),
    desde: str | None = Query(None),  # ej. 2026-01-01
    hasta: str | None = Query(None),  # ej. 2026-12-31
    admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = db.query(DataRadiacion).order_by(desc(DataRadiacion.Indice))

    if sensor_id:
        query = query.filter(DataRadiacion.SensorID == sensor_id)
    # CapturedTime es texto ISO8601 (ej. 2026-07-23T18:47:57Z), asi que
    # la comparacion como string funciona bien para filtrar por rango.
    if desde:
        query = query.filter(DataRadiacion.CapturedTime >= desde)
    if hasta:
        query = query.filter(DataRadiacion.CapturedTime <= hasta + "T23:59:59Z")

    filas = query.limit(50000).all()  # tope de seguridad para no tumbar el servidor

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "Indice", "SensorID", "SafecastUserID", "CapturedTime", "ValorCPM",
        "Pulso5Seg", "ConsecutivoLectura", "Validacion", "Latitude", "NorteSur",
        "Longitude", "EsteOeste", "AlturaNivelMar", "Sat", "Hdop", "Comprobacion",
    ])
    for f in filas:
        writer.writerow([
            f.Indice, f.SensorID, f.SafecastUserID, f.CapturedTime, f.ValorCPM,
            f.Pulso5Seg, f.ConsecutivoLectura, f.Validacion, f.Latitude, f.NorteSur,
            f.Longitude, f.EsteOeste, f.AlturaNivelMar, f.Sat, f.Hdop, f.Comprobacion,
        ])

    buffer.seek(0)
    nombre_archivo = "bgeigie_export"
    if sensor_id:
        nombre_archivo += f"_{sensor_id}"
    nombre_archivo += ".csv"

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{nombre_archivo}"'},
    )
