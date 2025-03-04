import requests

BASE_URL = "http://127.0.0.1:8000"

def create_user(email, password, account_type, school_id):
    user_data = {
        "email": email,
        "password": password,
        "account_type": account_type,
        "school_id": school_id
    }
    response = requests.post(f"{BASE_URL}/users/", json=user_data)
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to create user:", response.status_code, response.text)
        return None

def create_school(name, address, city, county, postcode, phone, website, domain):
    school_data = {
        "name": name,
        "address": address,
        "city": city,
        "county": county,
        "postcode": postcode,
        "phone": int(phone),  # Ensure phone is an integer
        "website": website,
        "domain": domain
    }
    response = requests.post(f"{BASE_URL}/schools/", json=school_data)
    if response.status_code == 200:
        try:
            return response.json()
        except requests.exceptions.JSONDecodeError:
            print("Failed to decode JSON response")
            return None
    else:
        print("Failed to create school:", response.status_code, response.text)
        print("Request payload:", school_data)
        return None

def create_session(school_id, school_name, supervisor_id, supervisor_email, client_id, client_email, date):
    session_data = {
        "school_id": school_id,
        "school": school_name,
        "supervisor_id": supervisor_id,
        "supervisor_email": supervisor_email,
        "client_id": client_id,
        "client_email": client_email,
        "date": date
    }
    response = requests.post(f"{BASE_URL}/sessions/", json=session_data)
    if response.status_code == 200:
        try:
            return response.json()
        except requests.exceptions.JSONDecodeError:
            print("Failed to decode JSON response")
            return None
    else:
        print("Failed to create session:", response.status_code, response.text)
        return None

if __name__ == "__main__":
    # Create 1 school
    school = create_school("Example School", "123 Main St", "Anytown", "Anystate", "12345", 1234567890, "www.example.com", "example.com")

    if school:
        # Create 3 users (2 supervisors and 1 client) with school_id
        supervisor1 = create_user("supervisor1@example.com", "password1", "supervisor", school["id"])
        supervisor2 = create_user("supervisor2@example.com", "password2", "supervisor", school["id"])
        client = create_user("client@example.com", "password3", "client", school["id"])

        if supervisor1 and supervisor2 and client:
            # Create 1 session with supervisor1 and supervisor2 connected to the school and session
            session = create_session(
                school_id=school["id"],
                school_name=school["name"],
                supervisor_id=supervisor2["id"],
                supervisor_email=supervisor2["email"],
                client_id=client["id"],
                client_email=client["email"],
                date="2023-10-01"
            )
            if session:
                print("Session created successfully:", session)