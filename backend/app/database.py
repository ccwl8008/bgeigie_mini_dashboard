from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker, declarative_base
 
from app.config import settings
 
# Se usa URL.create (en vez de armar el string a mano con f-strings) porque
# escapa automaticamente caracteres especiales en el usuario/password
# (@, :, /, #, etc.). Concatenar strings directo rompe la conexion si la
# contraseña tiene un "@", por ejemplo.
db_url = URL.create(
    "mysql+pymysql",
    username=settings.DB_USER,
    password=settings.DB_PASSWORD,
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    database=settings.DB_NAME,
    query={"charset": "utf8mb4"},
)
 
engine = create_engine(db_url, pool_pre_ping=True, pool_recycle=3600)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
 
 
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
 