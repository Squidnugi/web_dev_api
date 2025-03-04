import requests

BASE_URL = "http://127.0.0.1:8000"

def create_user(email, password, account_type, school_id=None):
    user_data = {
        "email": email,
        "password": password,
        "account_type": account_type
    }
    if school_id is not None:
        user_data["school_id"] = school_id

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
        "phone": phone,
        "website": website,
        "domain": domain
    }

    response = requests.post(f"{BASE_URL}/schools/", json=school_data)
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to create school:", response.status_code, response.text)
        return None

def create_session(school_id, supervisor_id, supervisor_email, client_id, client_email, date, additional_info):
    session_data = {
        "school_id": school_id,
        "supervisor_id": supervisor_id,
        "supervisor_email": supervisor_email,
        "client_id": client_id,
        "client_email": client_email,
        "date": date,
        "additional_info": additional_info
    }

    response = requests.post(f"{BASE_URL}/sessions/", json=session_data)
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to create session:", response.status_code, response.text)
        return None

if __name__ == "__main__":
    # Example usage
    client = create_user("johndoe@gmail.com", "johnpass", "admin", school_id=1)
    supervisor1 = create_user("supervisor@example.com", "supervisorpass", "supervisor")
    supervisor2 = create_user("supervisor2@example.com", "supervisorpass", "supervisor")
    school = create_school("School of Rock", "New York/New York/USA", "New York", "New York", "10001", 1234567890, "www.schoolofrock.com", "schoolofrock.com")
    session = create_session(school_id=school['id'], supervisor_id=supervisor1['id'], supervisor_email=supervisor1['email'], client_id=client['id'], client_email=client['email'], date="2023-10-10", additional_info="First session")