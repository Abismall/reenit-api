from pydantic import BaseSettings


class Settings(BaseSettings):
    database_hostname: str
    database_name: str
    database_port: str
    database_password: str
    database_username: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    dathost_username: str
    dathost_password: str

    class Config:
        env_file = ".env"


settings = Settings()
