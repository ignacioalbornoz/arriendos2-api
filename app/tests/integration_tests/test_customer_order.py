import pytest
import requests
import os
from supabase import create_client, Client
from faker import Faker
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

ENDPOINT = os.getenv("API_ENDPOINT")
RETURN = os.getenv("RETURN_URL")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_PATH = os.getenv("SUPABASE_PATH")
fake = Faker()


supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

customer = {"restaurant_id": None, "menu_items": []}


def perform_webpay_payment_credit_mastercard(driver, token, url):
    """
    Perform WebPay payment process using Selenium.

    Args:
        driver (webdriver.Chrome): Selenium WebDriver instance.
        token (str): Token for WebPay payment.
        url (str): URL for the WebPay payment page.
    """
    try:
        # Navigate to the base URL
        driver.get(url)

        # Create the form and submit it
        driver.execute_script(f"""
            var form = document.createElement('form');
            form.method = 'post';
            form.action = '{url}';

            var tokenField = document.createElement('input');
            tokenField.type = 'hidden';
            tokenField.name = 'token_ws';
            tokenField.value = '{token}';

            form.appendChild(tokenField);
            document.body.appendChild(form);
            form.submit();
        """)

        # Wait for a moment to ensure the request is processed
        driver.implicitly_wait(2)

        credito_button = driver.find_element(By.ID, "tarjetas")
        credito_button.click()

        driver.implicitly_wait(2)

        # Directly interact with input fields
        driver.find_element(By.ID, "card-number").send_keys("4051885600446623")

        card_image = driver.find_element(By.CLASS_NAME, "card")
        card_image.click()

        driver.implicitly_wait(1)

        driver.find_element(By.ID, "card-exp").send_keys(
            "1225"
        )  # Example expiration date
        driver.find_element(By.ID, "card-cvv").send_keys("123")

        # Wait for the "Pagar" button to be clickable
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(text(), 'Pagar')]")
            )
        ).click()

        driver.implicitly_wait(10)

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "paso")))

        WebDriverWait(driver, 10).until(
            EC.staleness_of(driver.find_element(By.ID, "paso"))
        )

        # Fill in the RUT and password fields
        driver.find_element(By.ID, "rutClient").send_keys("11.111.111-1")
        driver.find_element(By.ID, "passwordClient").send_keys("123")

        # Click the "Aceptar" button
        driver.find_element(By.XPATH, "//input[@value='Aceptar']").click()

        driver.implicitly_wait(3)
        driver.find_element(By.XPATH, "//input[@value='Continuar']").click()
        # Wait for the processing page to appear
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".voucher__head-title"))
        )

        # Check for the processing message
        WebDriverWait(driver, 30).until(
            EC.text_to_be_present_in_element(
                (By.CSS_SELECTOR, ".voucher__head-title"),
                "Estamos procesando tu pago",  # Ensure this message matches exactly
            )
        )

        # Wait until the form is submitted
        WebDriverWait(driver, 60).until(
            EC.invisibility_of_element_located((By.ID, "form"))
        )

        # Optionally, wait for the URL to change or a new page to load
        WebDriverWait(driver, 60).until(
            EC.url_changes(url)  # Check if the URL changes as a sign of completion
        )

        try:
            WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.ID, "proceed-button"))
            ).click()
        except Exception:
            print("Proceed button not clickable or missing.")

        print(f"Current URL: {driver.current_url}")
        return driver.current_url

    except Exception as e:
        print(f"An error occurred during the WebPay payment process: {e}")


@pytest.fixture(scope="module")
def clicomo_token():
    """
    A pytest fixture that creates a user in Supabase, signs in with the provided email and password,
    and returns the obtained token. The fixture is scoped to the module level.

    Returns:
        str: The obtained token.
    """
    email = fake.email()
    password = "password"

    supabase.auth.sign_up({"email": email, "password": password})

    # Create the user in Supabase
    response = supabase.auth.sign_in_with_password(
        {"email": email, "password": password}
    )

    token = response.session.access_token
    headers = {"access-token": token}
    response = requests.get(ENDPOINT + "/auth/email/login", headers=headers)
    assert response.status_code == 200
    clicomo_token = response.json()["token"]
    customer["clicomo_token"] = clicomo_token


def test_user_accept_terms(clicomo_token):
    """
    Test user accepting terms and conditions.

    Parameters:
    - clicomo_token (str): The token used for authentication.

    Returns:
    - None
    """
    headers = {"clicomo-token": customer["clicomo_token"]}
    terms_data = {"terms_accepted": True}
    response = requests.put(
        ENDPOINT + "/users/me/terms_and_conditions", json=terms_data, headers=headers
    )
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["terms_accepted"] == terms_data["terms_accepted"]


def test_get_user():
    """
    Test retrieving user information.

    Parameters:
    - clicomo_token (str): The token used for authentication.

    Returns:
    - None
    """
    headers = {"clicomo-token": customer["clicomo_token"]}
    response = requests.get(ENDPOINT + "/users/me", headers=headers)
    assert response.status_code == 200
    assert "display_name" in response.json()
    assert "email" in response.json()


def test_edit_user():
    """
    Test editing user information.

    Parameters:
    - clicomo_token (str): The token used for authentication.

    Returns:
    - None
    """
    headers = {"clicomo-token": customer["clicomo_token"]}
    new_data = {"display_name": "Test User", "phone_number": 1234567890}
    response = requests.put(ENDPOINT + "/users/me", json=new_data, headers=headers)
    assert response.status_code == 200
    updated_user = response.json()
    assert updated_user["display_name"] == new_data["display_name"]
    assert updated_user["phone_number"] == str(new_data["phone_number"])


def test_customer_get_restaurants():
    """
    Test retrieving a list of restaurants with optional filters.

    Parameters:
    - clicomo_token (str): The token used for authentication.

    Returns:
    - None
    """
    headers = {"clicomo-token": customer["clicomo_token"]}

    # Test without filters
    response = requests.get(f"{ENDPOINT}/restaurants", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)  # Should return a list of restaurants
    customer["restaurant_id"] = str(response.json()[0]["id"])

    # Test with `name` filter
    response = requests.get(
        f"{ENDPOINT}/restaurants?name=Test Restaurant", headers=headers
    )
    assert response.status_code == 200
    restaurants = response.json()
    assert isinstance(restaurants, list)
    if restaurants:
        assert any(
            "Test Restaurant" in restaurant["name"] for restaurant in restaurants
        )

    # Test with `only_open` filter set to False
    response = requests.get(f"{ENDPOINT}/restaurants?only_open=false", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    # Test with pagination (`skip` and `limit`)
    response = requests.get(f"{ENDPOINT}/restaurants?skip=0&limit=2", headers=headers)
    assert response.status_code == 200
    restaurants = response.json()
    assert isinstance(restaurants, list)
    assert len(restaurants) <= 2


def test_customer_get_tables():
    """
    Test retrieving a list of tables with pagination.

    Parameters:
    - clicomo_token (str): The token used for authentication.

    Returns:
    - None
    """
    headers = {
        "clicomo-token": customer["clicomo_token"],
        "Restaurant-ID": customer["restaurant_id"],
    }

    # Test without pagination parameters
    response = requests.get(f"{ENDPOINT}/tables", headers=headers)
    tables = response.json()
    assert response.status_code == 200
    assert isinstance(tables, list)
    customer["table_id"] = tables[0]["id"]

    # Test with specific pagination parameters
    response = requests.get(f"{ENDPOINT}/tables?skip=0&limit=5", headers=headers)
    assert response.status_code == 200
    tables = response.json()
    assert isinstance(tables, list)
    assert len(tables) <= 5

    # Test with invalid pagination parameters (negative skip)
    response = requests.get(f"{ENDPOINT}/tables?skip=-1&limit=5", headers=headers)
    assert response.status_code == 422


def test_customer_get_menu_items():
    """
    Fixture to fetch a menu item ID for testing.
    """
    headers = {
        "clicomo-token": customer["clicomo_token"],
        "Restaurant-ID": customer["restaurant_id"],
    }
    response = requests.get(f"{ENDPOINT}/menu_items", headers=headers)
    assert response.status_code == 200

    # Extract the menu item ID from the response
    menu_items_categories = response.json()
    for menu_items_category in menu_items_categories:
        menu_items = menu_items_category["menu_items"]
        for menu_item in menu_items:
            customer["menu_items"].append(menu_item["id"])


def test_create_order_with_menu_items_webpay_credit():
    """
    Test to create an order using a list of fetched menu item IDs.
    """
    headers = {
        "clicomo-token": customer["clicomo_token"],
        "Restaurant-ID": customer["restaurant_id"],
    }

    # Construct order details using fetched menu items
    order_details = [
        {"menu_item_id": item, "customizations": []} for item in customer["menu_items"]
    ]

    order_payload = {"details": order_details}
    table_id = customer["table_id"]
    response = requests.post(
        f"{ENDPOINT}/tables/{table_id}/orders/webpay",
        json=order_payload,
        headers=headers,
    )

    # Assertions to verify the response
    print(response.json())
    assert response.status_code == 200  # Or the expected status code

    # Extract token and URL from response
    token = response.json()["response"]["token"]
    url = response.json()["response"]["url"]

    options = webdriver.ChromeOptions()
    options.add_argument("--ignore-ssl-errors=yes")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--headless")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-web-security")  # Disable web security
    options.add_argument("--allow-insecure-localhost")
    options.add_argument("--disable-gpu")  # Disable GPU for headless mode
    options.add_argument("--disable-opentelemetry")
    options.add_argument("--window-size=1100,600")

    # Merge capabilities into options
    options.set_capability("browserName", "chrome")
    options.set_capability("acceptInsecureCerts", True)

    # Connect to the Selenium container
    driver = webdriver.Remote(
        command_executor="http://selenium:4444/wd/hub", options=options
    )

    try:
        # Call the refactored function to perform the WebPay payment process
        perform_webpay_payment_credit_mastercard(driver, token, url)

    finally:
        # Close the WebDriver session
        driver.quit()


def test_get_user_roles():
    """
    Test to get the list of roles associated with the user in different restaurants.
    """
    # Set up headers with any required authentication tokens or IDs
    headers = {"clicomo-token": customer["clicomo_token"]}

    # Make the GET request to the /me endpoint
    response = requests.get(ENDPOINT + "/roles/me", headers=headers)

    # Assert that the response status code is 200 (OK)
    # Optionally, you can also assert specific content in the response
    user_roles = response.json()
    print(user_roles)
    assert response.status_code == 200
    assert isinstance(user_roles, list)

    # Extract role names from the response
    role_names = [role["name"] for role in user_roles]
    assert "customer" not in role_names, "'customer' role found in user roles"
