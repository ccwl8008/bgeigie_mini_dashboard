-- =====================================================================
-- verify_data.sql
-- Corre esto DESPUES de restaurar tu backup, para detectar si el backup
-- realmente está completo o si se perdió algo en el camino.
--
-- Uso:
--   mysql -u root -p cyber2sof_bGeigie < verify_data.sql
-- =====================================================================

-- 1) La tabla existe y tiene la estructura esperada
SHOW TABLES LIKE 'Tabla_DataRadiacion';
DESCRIBE Tabla_DataRadiacion;

-- 2) Cuántos registros hay en total, y por sensor
SELECT COUNT(*) AS total_registros FROM Tabla_DataRadiacion;

SELECT SensorID, COUNT(*) AS lecturas,
       MIN(CapturedTime) AS primera_lectura,
       MAX(CapturedTime) AS ultima_lectura
FROM Tabla_DataRadiacion
GROUP BY SensorID;

-- 3) Huecos de datos: días sin ninguna lectura (compara contra lo que
--    tú esperarías si el sensor estuvo corriendo continuamente)
SELECT DATE(STR_TO_DATE(CapturedTime, '%Y-%m-%dT%H:%i:%sZ')) AS dia,
       COUNT(*) AS lecturas_ese_dia
FROM Tabla_DataRadiacion
WHERE CapturedTime IS NOT NULL AND CapturedTime <> ''
GROUP BY dia
ORDER BY dia;

-- 4) Consecutivos de lectura duplicados o fuera de orden por sensor
--    (si el bGeigie numera sus lecturas, un salto grande indica
--    registros faltantes; duplicados indican reinserciones)
SELECT SensorID, ConsecutivoLectura, COUNT(*) AS repeticiones
FROM Tabla_DataRadiacion
GROUP BY SensorID, ConsecutivoLectura
HAVING repeticiones > 1;

-- 5) Registros con campos clave vacíos o nulos (posible corrupción
--    parcial en el backup/restore)
SELECT COUNT(*) AS registros_incompletos
FROM Tabla_DataRadiacion
WHERE SensorID IS NULL OR SensorID = ''
   OR CapturedTime IS NULL OR CapturedTime = ''
   OR ValorCPM IS NULL;

-- 6) Rango real de valores CPM (para detectar valores absurdos que
--    delaten una migración corrupta, ej. CPM negativos o gigantes)
SELECT MIN(ValorCPM) AS cpm_min, MAX(ValorCPM) AS cpm_max, AVG(ValorCPM) AS cpm_prom
FROM Tabla_DataRadiacion;
