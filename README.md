# bGeigie Dashboard

Reemplazo del stack original en PHP (`bGeigieConexion.php`, `bGeigiePost.php`,
`bGeigieVisualizar.php`) por un proyecto Dockerizado para Coolify:

- **MariaDB** con los datos migrados de tu backup.
- **Backend en Python (FastAPI)** que:
  - Recibe las lecturas del bGeigie en `/bGeigiePost.php` (mismo path y
    mismos campos que ya usa tu dispositivo — no hay que tocar el firmware),
    pero usando parámetros en vez de concatenar SQL (el .php original era
    vulnerable a inyección SQL).
  - Sirve un dashboard con login en `/`.
- **Login por usuario** (tabla `Usuario`, contraseñas con bcrypt, sesión
  por cookie firmada). Queda listo para varios usuarios aunque arranca con
  un solo admin.
- **Visualización**: gauge tipo instrumento con el CPM/µSv actual, gráfica
  de CPM en el tiempo, mapa con las coordenadas de cada lectura, y tabla de
  últimos registros. Se actualiza solo cada 10s (ya no es el
  `<meta refresh>` de página completa del .php original).

## 1. Desplegar en Coolify

1. Sube esta carpeta a un repo de git (Coolify puede desplegar desde ahí),
   o pégala como recurso "Docker Compose" directo en Coolify.
2. Copia `.env.example` a `.env` y define ahí los valores reales:
   - `MYSQL_ROOT_PASSWORD`, `MYSQL_USER`, `MYSQL_PASSWORD`
   - `SECRET_KEY` (genera una con `openssl rand -hex 32`)
   - `ADMIN_USERNAME` / `ADMIN_PASSWORD` (el primer usuario que podrá
     entrar al dashboard)
3. En Coolify, configura el dominio que ya tienes apuntado por DNS hacia
   el servicio `backend` (puerto interno 8000; Traefik ya está declarado
   en las labels del `docker-compose.yml`).
4. Despliega. Al arrancar, el backend:
   - Crea las tablas si no existen (no pisa nada si ya restauraste tu backup).
   - Crea el usuario admin definido en `.env`, si no existe todavía.

## 2. Migrar tu backup

Como no estás 100% seguro de que el backup quedó completo, el proceso
incluye verificación automática:

```bash
cd migration
export MYSQL_ROOT_PASSWORD=<la_misma_del_.env>
export MYSQL_DATABASE=cyber2sof_bGeigie
./restore_backup.sh /ruta/a/tu_backup.sql
```

Esto restaura el `.sql` dentro del contenedor `bgeigie-db` y corre
`verify_data.sql`, que te muestra:

- Total de registros y rango de fechas por sensor.
- **Días sin ninguna lectura** (para detectar huecos si el sensor debía
  estar corriendo continuamente).
- Consecutivos de lectura duplicados (reinserciones) o con saltos raros.
- Registros con campos clave vacíos (corrupción parcial).
- Rango de valores CPM (para detectar basura numérica).

Si algo se ve mal ahí, el problema está en el backup en sí — vale la pena
volver a exportarlo del servidor viejo (Mochahost) si todavía sigue
accesible, en vez de confiar en el que ya tienes.

Puedes volver a correr `verify_data.sql` solo, en cualquier momento:

```bash
docker exec -i bgeigie-db mysql -uroot -p"$MYSQL_ROOT_PASSWORD" cyber2sof_bGeigie < migration/verify_data.sql
```

## 3. Agregar más usuarios de acceso

Por ahora no hay una pantalla de "crear usuario" en el dashboard (a
propósito, para no abrir registro público). Para agregar a alguien más,
entra al contenedor y usa Python directo:

```bash
docker exec -it bgeigie-backend python -c "
from app.database import SessionLocal
from app.models import Usuario
from app.security import hash_password

db = SessionLocal()
db.add(Usuario(username='nuevo_usuario', password_hash=hash_password('su_clave'), nombre_completo='Nombre Completo', activo=1))
db.commit()
"
```

## 4. Estructura del proyecto

```
bgeigie-dashboard/
├── docker-compose.yml
├── .env.example
├── db/init/001_schema.sql        # esquema (tabla original + Usuario)
├── migration/
│   ├── restore_backup.sh         # restaura tu backup + corre verificación
│   └── verify_data.sql           # queries de auditoría de integridad
└── backend/
    ├── Dockerfile
    ├── requirements.txt
    └── app/
        ├── main.py                # arranque, crea tablas, siembra admin
        ├── config.py
        ├── database.py
        ├── models.py
        ├── security.py            # hash de contraseñas + sesión firmada
        ├── nmea.py                 # conversión de coordenadas GPS
        ├── routers/
        │   ├── ingest.py           # POST del bGeigie (reemplaza bGeigiePost.php)
        │   ├── auth.py             # login/logout
        │   └── dashboard.py        # página + API JSON para el front
        ├── templates/              # login.html, dashboard.html
        └── static/                 # CSS del panel + JS del dashboard
```

## Notas de seguridad respecto al proyecto original

- Las credenciales de base de datos ya no están hardcodeadas en el código
  (estaban en texto plano en `bGeigieConexion.php`) — ahora vienen de
  variables de entorno.
- El INSERT de `bGeigiePost.php` concatenaba los `$_POST` directo en el
  SQL (inyección SQL abierta). El nuevo endpoint usa el ORM con
  parámetros.
- El dashboard viejo era público sin autenticación; ahora exige login y
  usa cookies de sesión firmadas (no se puede falsificar sin la
  `SECRET_KEY`).

## Notas sobre la conversión de coordenadas

El bGeigie guarda latitud/longitud en formato NMEA crudo (`ddmm.mmmm` +
letra de hemisferio), tal como sale del GPS. `app/nmea.py` las convierte a
grados decimales para el mapa. Si tus lecturas vienen en un formato
distinto, revisa esa lógica antes de confiar en las posiciones del mapa.
