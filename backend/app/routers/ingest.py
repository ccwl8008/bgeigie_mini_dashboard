from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import DataRadiacion

router = APIRouter()


@router.post("/bGeigiePost.php")  # mismo path que el dispositivo ya usa
@router.post("/api/ingest")       # alias más limpio para configs nuevas
async def ingest_reading(
    db: Session = Depends(get_db),
    sensorID: str = Form(None),
    safecastUserID: str = Form(None),
    capturedTime: str = Form(None),
    valorCPM: int = Form(None),
    pulso5Seg: int = Form(None),
    consecutivoLectura: int = Form(None),
    validacion: str = Form(None),
    latitude: str = Form(None),
    norteSur: str = Form(None),
    longitude: str = Form(None),
    esteOeste: str = Form(None),
    alturaNivelMar: str = Form(None),
    sat: int = Form(None),
    hdop: str = Form(None),
    comprobacion: str = Form(None),
):
    """Recibe exactamente los mismos campos POST que bGeigiePost.php,
    para que el dispositivo/firmware no necesite ningún cambio.
    A diferencia del original, usa el ORM con parámetros (no concatena
    strings en el SQL), así que queda cerrada la inyección SQL que tenía
    el .php."""

    registro = DataRadiacion(
        SensorID=sensorID,
        SafecastUserID=safecastUserID,
        CapturedTime=capturedTime,
        ValorCPM=valorCPM,
        Pulso5Seg=pulso5Seg,
        ConsecutivoLectura=consecutivoLectura,
        Validacion=validacion,
        Latitude=latitude,
        NorteSur=norteSur,
        Longitude=longitude,
        EsteOeste=esteOeste,
        AlturaNivelMar=alturaNivelMar,
        Sat=sat,
        Hdop=hdop,
        Comprobacion=comprobacion,
    )
    db.add(registro)
    db.commit()

    return {"status": "ok", "mensaje": "Registro guardado correctamente"}
