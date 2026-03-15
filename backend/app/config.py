"""Configurações da aplicação via variáveis de ambiente."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings carregadas de variáveis de ambiente ou arquivo .env."""

    # Supabase
    SUPABASE_URL: str = "postgresql://localhost:5432/financeiro"
    SUPABASE_KEY: str = ""

    # JWT
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    # App
    APP_NAME: str = "Controle Financeiro API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    @property
    def cors_origins_list(self) -> list[str]:
        """Retorna lista de origens CORS a partir da string separada por vírgula."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
