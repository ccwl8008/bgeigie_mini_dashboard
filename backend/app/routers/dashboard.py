from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models import DataRadiacion, Usuario
from app.security import get_current_username
from app.nmea import parse_latitude, parse_longitude
from app.templates_config import templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    username: str = Depends(get_current_username),
    db: Session = Depends(get_db),
):
    usuario = db.query(Usuario).filter(Usuario.username == username).first()
    es_admin = bool(usuario and usuario.es_admin)
    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "username": username, "es_admin": es_admin}
    )


@router.get("/api/stats")
async def stats(
    username: str = Depends(get_current_username),
    db: Session = Depends(get_db),
):
    ultimo = (
        db.query(DataRadiacion)
        .order_by(desc(DataRadiacion.Indice))
        .first()
    )
    total = db.query(DataRadiacion).count()

    if not ultimo:
        return {"ultima_lectura": None, "total_registros": total}

    cpm = ultimo.ValorCPM or 0
    return {
        "sensorID": ultimo.SensorID,
        "capturedTime": ultimo.CapturedTime,
        "valorCPM": cpm,
        "microSieverthora": round(cpm / 334, 4),
        "sat": ultimo.Sat,
        "hdop": ultimo.Hdop,
        "total_registros": total,
    }


@router.get("/api/readings")
async def readings(
    limit: int = Query(50, le=500),
    sensor_id: str | None = Query(None, alias="sensorID"),
    username: str = Depends(get_current_username),
    db: Session = Depends(get_db),
):
    query = db.query(DataRadiacion).order_by(desc(DataRadiacion.Indice))
    if sensor_id:
        query = query.filter(DataRadiacion.SensorID == sensor_id)

    rows = query.limit(limit).all()

    resultado = []
    for r in rows:
        resultado.append({
            "indice": r.Indice,
            "sensorID": r.SensorID,
            "safecastUserID": r.SafecastUserID,
            "capturedTime": r.CapturedTime,
            "valorCPM": r.ValorCPM,
            "microSieverthora": round((r.ValorCPM or 0) / 334, 4),
            "pulso5Seg": r.Pulso5Seg,
            "consecutivoLectura": r.ConsecutivoLectura,
            "latitude": parse_latitude(r.Latitude, r.NorteSur),
            "longitude": parse_longitude(r.Longitude, r.EsteOeste),
            "alturaNivelMar": r.AlturaNivelMar,
            "sat": r.Sat,
            "hdop": r.Hdop,
        })

    # el front espera orden cronológico ascendente para la gráfica
    resultado.reverse()
    return resultado


@router.get("/api/sensores")
async def sensores(
    username: str = Depends(get_current_username),
    db: Session = Depends(get_db),
):
    filas = db.query(DataRadiacion.SensorID).distinct().all()
    return [f[0] for f in filas if f[0]]
