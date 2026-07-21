-- Esquema para bGeigie Dashboard
-- Recrea la tabla original Tabla_DataRadiacion (compatible con los datos migrados)
-- y agrega la tabla Usuario para el control de acceso.

CREATE TABLE IF NOT EXISTS Tabla_DataRadiacion (
    Indice              INT AUTO_INCREMENT PRIMARY KEY,
    SensorID            VARCHAR(50),
    SafecastUserID      VARCHAR(50),
    CapturedTime        VARCHAR(50),
    ValorCPM            INT,
    Pulso5Seg           INT,
    ConsecutivoLectura  INT,
    Validacion          VARCHAR(10),
    Latitude            VARCHAR(20),
    NorteSur            CHAR(1),
    Longitude           VARCHAR(20),
    EsteOeste           CHAR(1),
    AlturaNivelMar      VARCHAR(20),
    Sat                 INT,
    Hdop                VARCHAR(20),
    Comprobacion        VARCHAR(20),
    creado_en           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_sensor_time (SensorID, CapturedTime),
    INDEX idx_consecutivo (SensorID, ConsecutivoLectura)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS Usuario (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    username        VARCHAR(50) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    nombre_completo VARCHAR(100),
    activo          TINYINT(1) DEFAULT 1,
    creado_en       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
