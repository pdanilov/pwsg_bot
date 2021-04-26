from pathlib import Path

from envparse import env, ConfigurationError

dotenv = Path(__file__).parent.parent / '.env'
if dotenv.is_file():
    env.read_envfile(path=dotenv)

BOT_TOKEN = env.str('BOT_TOKEN')
GOOGLE_MAPS_API_KEY = env.str('GOOGLE_MAPS_API_KEY')
REDIS_URL = env.str('REDIS_URL')
DATABASE_URL = env.str('DATABASE_URL')

schema = 'postgresql'
try:
    dialect = env.str('POSTGRES_DIALECT')
    schema += f'+{dialect}'
except ConfigurationError:
    pass

POSTGRESQL_URI = DATABASE_URL.replace('postgres', schema, 1)
