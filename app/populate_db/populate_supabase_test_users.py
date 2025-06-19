import os
from supabase import create_client

# Environment variables for Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_PATH = os.getenv("SUPABASE_PATH")

# Create Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def create_supabase_test_user(email: str, password: str):
    try:
        # Attempt to sign up the user
        response = supabase.auth.sign_up({"email": email, "password": password})
        print(f"User created: {email}")
        return response
    except Exception as e:
        # Handle any errors (e.g., user already exists) and continue
        print(f"Failed to create user {email}: {e}")


def test_users_supabase_setup():
    # List of users to create
    users = [
        {"email": "admin@clicomo.app", "password": "password"},
        {"email": "section.master.cocina@clicomo.app", "password": "password"},
        {"email": "section.master.cafeteria@clicomo.app", "password": "password"},
        {"email": "runner@clicomo.app", "password": "password"},
    ]

    for user in users:
        create_supabase_test_user(user["email"], user["password"])
