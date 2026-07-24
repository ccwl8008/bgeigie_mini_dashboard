from sqlalchemy import Column, Integer, String, TIMESTAMP, func

from app.database import Base


class DataRadiacion(Base):
    """Mapea la tabla original Tabla_DataRadiacion (sin cambiar su forma,
    para que los datos migrados encajen tal cual)."""

    __tablename__ = "Tabla_DataRadiacion"

    Indice = Column(Integer, primary_key=True, autoincrement=True)
    SensorID = Column(String(50))
    SafecastUserID = Column(String(50))
    CapturedTime = Column(String(50))
    ValorCPM = Column(Integer)
    Pulso5Seg = Column(Integer)
    ConsecutivoLectura = Column(Integer)
    Validacion = Column(String(10))
    Latitude = Column(String(20))
    NorteSur = Column(String(1))
    Longitude = Column(String(20))
    EsteOeste = Column(String(1))
    AlturaNivelMar = Column(String(20))
    Sat = Column(Integer)
    Hdop = Column(String(20))
    Comprobacion = Column(String(20))
    creado_en = Column(TIMESTAMP, server_default=func.now())


class Usuario(Base):
    __tablename__ = "Usuario"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    nombre_completo = Column(String(100))
    activo = Column(Integer, default=1)
    es_admin = Column(Integer, default=0)
    creado_en = Column(TIMESTAMP, server_default=func.now())
