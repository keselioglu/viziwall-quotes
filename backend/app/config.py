from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str
    secret_key: str
    access_token_expire_minutes: int = 480
    company_name: str = "Viziwall"
    company_email: str = ""
    company_address: str = ""
    company_logo_path: str = ""


settings = Settings()
