from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "logistics"
    postgres_user: str = "logistics"
    postgres_password: str = "logistics"

    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "logistics_events"

    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"
    rabbitmq_exchange: str = "logistics.events"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
