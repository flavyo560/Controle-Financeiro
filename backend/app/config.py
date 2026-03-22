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

    # Frontend URL (para redirecionamentos Stripe)
    FRONTEND_URL: str = ""

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_SIMPLES_MENSAL: str = ""
    STRIPE_PRICE_SIMPLES_ANUAL: str = ""
    STRIPE_PRICE_PLUS_MENSAL: str = ""
    STRIPE_PRICE_PLUS_ANUAL: str = ""

    # Resend (email)
    RESEND_API_KEY: str = ""

    # App
    APP_NAME: str = "Controle Financeiro API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    @property
    def stripe_prices(self) -> dict[str, str]:
        """Retorna mapeamento plano_ciclo → price_id do Stripe."""
        return {
            "simples_mensal": self.STRIPE_PRICE_SIMPLES_MENSAL,
            "simples_anual": self.STRIPE_PRICE_SIMPLES_ANUAL,
            "plus_mensal": self.STRIPE_PRICE_PLUS_MENSAL,
            "plus_anual": self.STRIPE_PRICE_PLUS_ANUAL,
        }

    @property
    def cors_origins_list(self) -> list[str]:
        """Retorna lista de origens CORS a partir da string separada por vírgula."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
