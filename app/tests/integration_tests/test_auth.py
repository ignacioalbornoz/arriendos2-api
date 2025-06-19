import os
from faker import Faker
from supabase import create_client, Client
import requests

ENDPOINT = os.getenv("API_ENDPOINT")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_PATH = os.getenv("SUPABASE_PATH")
fake = Faker()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def test_auth_with_old_user():
    headers = {"google-token": "asdfkljasfd;l"}
    response = requests.get(ENDPOINT + "/auth/google/login", headers=headers)
    print(response.json())
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."
    pass


def test_sign_in_app_user():
    # Create the user in Supabase
    response = supabase.auth.sign_in_with_password(
        {"email": "admin@clicomo.app", "password": "password"}
    )

    token = response.session.access_token
    headers = {"access-token": "asdfkljasfd;l"}
    response = requests.get(ENDPOINT + "/auth/email/login", headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."

    headers = {"access-token": token}
    response = requests.get(ENDPOINT + "/auth/email/login", headers=headers)
    print(response.json())
    assert response.status_code == 200
    assert response.json()["token"] is not None


def test_create_sign_in_random_user():
    email = fake.email()
    password = "password"

    supabase.auth.sign_up({"email": email, "password": password})

    # Create the user in Supabase
    response = supabase.auth.sign_in_with_password(
        {"email": email, "password": password}
    )

    token = response.session.access_token
    headers = {"access-token": "asdfkljasfd;l"}
    response = requests.get(ENDPOINT + "/auth/email/login", headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."

    headers = {"access-token": token}
    response = requests.get(ENDPOINT + "/auth/email/login", headers=headers)
    print(response.json())
    assert response.status_code == 200
    assert response.json()["token"] is not None
