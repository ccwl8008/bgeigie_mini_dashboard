import os


class Settings:
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_NAME: str = os.getenv("DB_NAME", "cyber2sof_bGeigie")
    DB_USER: str = os.getenv("DB_USER", "cyber2sof_nano")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")

    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-cambia-esto")

    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "")
    ADMIN_NOMBRE: str = os.getenv("ADMIN_NOMBRE", "Administrador")

    SESSION_COOKIE_NAME: str = "bgeigie_session"
    SESSION_MAX_AGE_SECONDS: int = 60 * 60 * 12  # 12 horas

    @property
    def sqlalchemy_url(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )


settings = Settings()
