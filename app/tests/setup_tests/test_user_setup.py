import os
from supabase import create_client, Client


ENDPOINT = os.getenv("API_ENDPOINT")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_PATH = os.getenv("SUPABASE_PATH")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


### CORRER ESTO PARA CREAR USUARIOS EN SUPABASE AUTH TABLE, SI YA ESTAN CREADOS NO CORRER ESTE TEST
def users_setup():
    # Create the user in Supabase
    supabase.auth.sign_up({"email": "admin@clicomo.app", "password": "password"})
    supabase.auth.sign_up(
        {"email": "section.master.cocina@clicomo.app", "password": "password"}
    )
    supabase.auth.sign_up(
        {"email": "section.master.cafeteria@clicomo.app", "password": "password"}
    )
    supabase.auth.sign_up({"email": "runner@clicomo.app", "password": "password"})
