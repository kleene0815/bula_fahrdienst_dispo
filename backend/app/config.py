from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Datenbank
    database_url: str = "postgresql+asyncpg://user:password@localhost/fahrdienst"

    # Keycloak
    keycloak_url: str = "https://keycloak.example.com"
    keycloak_realm: str = "myrealm"

    # CORS — kommagetrennte Liste erlaubter Origins
    cors_origins: list[str] = ["http://localhost:5173"]

    @property
    def keycloak_jwks_url(self) -> str:
        return f"{self.keycloak_url}/realms/{self.keycloak_realm}/protocol/openid-connect/certs"

    @property
    def keycloak_issuer(self) -> str:
        return f"{self.keycloak_url}/realms/{self.keycloak_realm}"


settings = Settings()
