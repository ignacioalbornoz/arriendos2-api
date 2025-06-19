import pytest
import requests
import os
from supabase import create_client, Client


ENDPOINT = os.getenv("API_ENDPOINT")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_PATH = os.getenv("SUPABASE_PATH")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

admin = {"restaurant_id": None}


@pytest.fixture(scope="module")
def clicomo_token():
    """
    A pytest fixture that creates a user in Supabase, signs in with the provided email and password,
    and returns the obtained token. The fixture is scoped to the module level.

    Returns:
        str: The obtained token.
    """
    # Create the user in Supabase and get the token
    response = supabase.auth.sign_in_with_password(
        {"email": "admin@clicomo.app", "password": "password"}
    )

    token = response.session.access_token

    headers = {"access-token": token}
    response = requests.get(ENDPOINT + "/auth/email/login", headers=headers)
    assert response.status_code == 200

    clicomo_token = response.json()["token"]

    return clicomo_token


def test_restaurants_me_admin(clicomo_token):
    """
    This function tests the 'restaurants/me' endpoint with an admin role. It takes a 'clicomo_token' as a parameter, which is used to authenticate the request. The function sends a GET request to the specified endpoint with the provided headers and retrieves the response. The response is then checked for a status code of 200. If the status code is 200, the restaurant ID of the first restaurant in the response is extracted and stored in the 'admin' dictionary under the key 'restaurant_id'.

    Parameters:
    - clicomo_token (str): The token used for authentication.

    Returns:
    - None
    """
    headers = {"clicomo-token": clicomo_token}
    response = requests.get(
        ENDPOINT + "/restaurants/me?role=admin&skip=0&limit=100", headers=headers
    )
    data = response.json()
    assert response.status_code == 200
    admin["restaurant_id"] = data[0].get("restaurant").get("id")
