import requests

BASE_URL = "http://127.0.0.1:8000"

def create_user(email, password):
    response = requests.post(f"{BASE_URL}/users/", json={"email": email, "password": password})
    if response.status_code == 200:
        print("User created successfully:", response.json())
    else:
        print("Failed to create user:", response.status_code, response.json())

def get_user(email):
    response = requests.get(f"{BASE_URL}/users/{email}")
    if response.status_code == 200:
        print("User details:", response.json())
    else:
        print("User not found:", response.status_code, response.json())

def get_all_users():
    response = requests.get(f"{BASE_URL}/users/")
    if response.status_code == 200:
        print("All users:", response.json())
    else:
        print("Failed to retrieve users:", response.status_code, response.json())

def delete_user(user_id):
    response = requests.delete(f"{BASE_URL}/users/{user_id}")
    if response.status_code == 200:
        print("User deleted successfully:", response.json())
    else:
        print("Failed to delete user:", response.status_code, response.json())

if __name__ == "__main__":
    # Example usage
    create_user("johndoe@gmail.com", "johnpass")
    get_user("johndoe@gmail.com")
    get_all_users()
    delete_user(1)