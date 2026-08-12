import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    openweather_api_key: str = os.getenv("OPENWEATHER_API_KEY", "")
    tavily_api_key: str = os.getenv("TAVILY_API_KEY", "")
    resend_api_key: str = os.getenv("RESEND_API_KEY", "")
    resend_from_email: str = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")

    model_name: str = os.getenv("MODEL_NAME", "claude-sonnet-5")
    max_agent_rounds: int = int(os.getenv("MAX_AGENT_ROUNDS", "6"))
    tool_timeout_seconds: float = float(os.getenv("TOOL_TIMEOUT_SECONDS", "8"))

    cors_origins: list[str] = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")


settings = Settings()
