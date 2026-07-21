#!/usr/bin/env bash
# =============================================================================
# restore_backup.sh
#
# Restaura tu backup .sql dentro del contenedor MariaDB de este proyecto de
# Coolify, y corre automáticamente verify_data.sql para que puedas ver de
# entrada si el backup quedó completo o si hay huecos/datos raros.
#
# Uso:
#   ./restore_backup.sh /ruta/a/tu_backup.sql
#
# Requisitos: el stack de docker-compose de este proyecto ya debe estar
# corriendo en Coolify (el servicio se llama "db" en docker-compose.yml).
# =============================================================================
set -euo pipefail

if [ $# -ne 1 ]; then
    echo "Uso: $0 /ruta/a/tu_backup.sql"
    exit 1
fi

BACKUP_FILE="$1"
CONTAINER_NAME="${DB_CONTAINER:-bgeigie-db}"
DB_NAME="${MYSQL_DATABASE:-cyber2sof_bGeigie}"
DB_ROOT_PASS="${MYSQL_ROOT_PASSWORD:?Define MYSQL_ROOT_PASSWORD en tu entorno o .env}"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "No encuentro el archivo: $BACKUP_FILE"
    exit 1
fi

echo ">> Copiando backup dentro del contenedor..."
docker cp "$BACKUP_FILE" "${CONTAINER_NAME}:/tmp/backup.sql"

echo ">> Restaurando dentro de la base ${DB_NAME}..."
docker exec -i "$CONTAINER_NAME" sh -c "mysql -uroot -p${DB_ROOT_PASS} ${DB_NAME} < /tmp/backup.sql"

echo ">> Restauración terminada. Corriendo verificación..."
docker cp "$(dirname "$0")/verify_data.sql" "${CONTAINER_NAME}:/tmp/verify_data.sql"
docker exec -i "$CONTAINER_NAME" sh -c "mysql -uroot -p${DB_ROOT_PASS} ${DB_NAME} < /tmp/verify_data.sql"

echo ""
echo "=================================================================="
echo " Revisa arriba: conteo de registros por sensor, huecos por día,"
echo " consecutivos duplicados y valores CPM fuera de rango."
echo " Si algo se ve incompleto, es el backup el que falló, no la"
echo " migración: vale la pena volver a exportar desde el server viejo"
echo " si todavía está disponible."
echo "=================================================================="
