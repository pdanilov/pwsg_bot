from pathlib import Path

from envparse import ConfigurationError, env

dotenv = Path(__file__).parent.parent / ".env"
env.read_envfile(path=dotenv)

BOT_TOKEN = env.str("BOT_TOKEN")
GOOGLE_MAPS_API_KEY = env.str("GOOGLE_MAPS_API_KEY")
REDIS_HOST = env.str("REDIS_HOST")
REDIS_PORT = env.str("REDIS_PORT")
POSTGRES_HOST = env.str("POSTGRES_HOST")
POSTGRES_PORT = env.str("POSTGRES_PORT")
POSTGRES_USER = env.str("POSTGRES_USER")
POSTGRES_PASSWORD = env.str("POSTGRES_PASSWORD")
POSTGRES_DB = env.str("POSTGRES_DB")
POSTGRES_DIALECT = env.str("POSTGRES_DIALECT")

schema = "postgresql"
try:
    schema += f"+{POSTGRES_DIALECT}"
except ConfigurationError:
    pass

POSTGRES_URI = (
    f"{schema}://"
    f"{POSTGRES_USER}:"
    f"{POSTGRES_PASSWORD}@"
    f"{POSTGRES_HOST}:"
    f"{POSTGRES_PORT}/"
    f"{POSTGRES_DB}"
)
