from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Definición de la base declarativa para los modelos ORM
Base = declarative_base()

DATABASE_USER = os.getenv("POSTGRES_USER")
DATABASE_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DATABASE_HOST = os.getenv("POSTGRES_HOST")
DATABASE_NAME = os.getenv("POSTGRES_DB")
DATABASE_PORT = os.getenv("POSTGRES_PORT")

required_vars = {
    "DATABASE_USER": DATABASE_USER,
    "DATABASE_PASSWORD": DATABASE_PASSWORD,
    "DATABASE_HOST": DATABASE_HOST,
    "DATABASE_NAME": DATABASE_NAME,
    "DATABASE_PORT": DATABASE_PORT,
}

# Comprobar si alguna de ellas es None
for var_name, var_value in required_vars.items():
    if var_value is None or var_value == "":
        raise EnvironmentError(f"La variable de entorno '{var_name}' no está definida.")

# Crea el motor de la base de datos SQLAlchemy
database_url = f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
# engine = create_engine(database_url, echo=True)
engine = create_engine(database_url, echo=False)


# # Define el manejador del evento `engine_connect`
# @event.listens_for(engine, "engine_connect")
# def set_timezone(connection, branch):
#     """
#     Sets the timezone for the database connection.

#     This function is an event listener for the 'engine_connect' event. It checks if the connection is a sub-connection (i.e., within a transaction) and if so, does nothing. Otherwise, it attempts to set the timezone to 'America/Santiago'. If an error occurs during this process, it allows SQLAlchemy to attempt reconnection.

#     Parameters:
#         connection (object): The database connection object.
#         branch (bool): A boolean indicating whether the connection is a sub-connection.

#     Returns:
#         None
#     """
#     if branch:
#         # Cuando branch es True, la conexión es una "subconexión" de una conexión ya existente,
#         # por ejemplo, dentro de una transacción. En este caso, no necesitas hacer nada.
#         return
#     try:
#         # Intenta establecer la zona horaria
#         connection.execution_options(isolation_level="AUTOCOMMIT")
#         connection.execute("SET TIME ZONE 'America/Santiago'")
#     except exc.DBAPIError as err:
#         # Si ocurre un error al establecer la zona horaria, como una desconexión,
#         # no interceptes el error. Deja que SQLAlchemy intente reconectar.
#         if err.connection_invalidated:
#             pass
#         else:
#             raise


# Configuración de la sesión ORM
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Función para obtener una sesión de base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


"""
from sqlalchemy_utils import database_exists, create_database, drop_database

database_url_without_db = f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/postgres"
# Crea un engine para conectarse a `postgres`
engine = create_engine(database_url_without_db, isolation_level="AUTOCOMMIT")

with engine.connect() as conn:
    conn.execute(f"SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '{DATABASE_NAME}' AND pid <> pg_backend_pid();")
    # Elimina la base de datos si existe
    if database_exists(database_url):
        drop_database(database_url)
        print(f"Database {DATABASE_NAME} dropped.")
    # Crea la base de datos
    create_database(database_url)
    print(f"Database {DATABASE_NAME} created.")

# Ahora puedes crear un nuevo engine para la base de datos específica y continuar con la inicialización
engine = create_engine(database_url, echo=True)
"""
