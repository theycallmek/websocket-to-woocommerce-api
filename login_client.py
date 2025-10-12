import time
from datetime import datetime
import dotenv
import httpx
import machineid


dotenv.load_dotenv()

USERNAME = "test1"
PASSWORD = "swadbotpass123"
# This is the password required by the JWT plugin
# APP_PASSWORD = "ZgKzpENVHMBnjouSDPNRmP6o"

#URL = "https://fastapi-license-server-meh3ibmmpq-uc.a.run.app"
URL = 'http://127.0.0.1:8000'


def get_session_id():
    return f'{machineid.id()}-{str(datetime.now().timestamp()).replace(".", "-")}'


def get_my_ip():
    with httpx.Client() as client:
        response = client.get("https://api.ipify.org")
    if response.status_code == 200:
        return response.text
    return "0.0.0.0"


this_session = get_session_id()
client_ip = get_my_ip()

def main():
    print("RUNNING MAIN")
    # POST to /login
    with httpx.Client(timeout=20) as client:
        response = client.post(
            url=f"{URL}/login",
            # Use the Application Password for the JWT plugin
            params={"user_login": USERNAME, "user_pass": PASSWORD},
        )
    if response.status_code != 200:
        print(f"response.status_code: {response.status_code}")
        print(response.content)
        return False
    token_data = response.json()
    print(f"TOKEN DATA: {token_data}")

    # POST to /license/activate
    params = {
        "username": token_data["user_nicename"],
        "client_id": token_data["user_id"],
        "token": token_data["token"],
        "session_id": this_session,
        "client_ip": client_ip
    }
    with httpx.Client() as client:
        response = client.post(url=f"{URL}/license/activate", params=params, timeout=20)
    if response.status_code != 200:
        print(f"{response.status_code} STATUS CODE (/license/activate) {response.content}")
        return False
    license_activate_data = response.json()
    print(f'LICENSE ACTIVATE DATA: {license_activate_data["message"]}')
    if license_activate_data["success"] is False:
        return False
    r = 10
    for i in range(r):
        print(f"==============\nPASS: {i + 1}/{r}")
        time.sleep(15)
        # POST to /license/status
        with httpx.Client() as client:
            # params["token"] = params["token"] + "0"
            params["token"] = params["token"]
            response = client.post(
                url=f"{URL}/license/status", params=params, timeout=20
            )
        if response.status_code != 200:
            print("WRONG STATUS CODE (/license/status)")
            return False
        license_status_data = response.json()
        if license_status_data["success"] is False:
            print(f'ACTIVATION FAILED!: {license_status_data}')
            return False
        print(f"LICENSE STATUS DATA: {license_status_data}")
        if i >= 9:
            print("DONE!")

    # time.sleep(5)
    #
    # with httpx.Client() as client:
    #     response = client.post(url=f'{URL}/license/deactivate', params=params)
    # if response.status_code != 200:
    #     print('WRONG STATUS CODE (/license/deactivate)')
    #     return False
    # license_deactivate_data = response.json()
    # print(f'LICENSE DEACTIVATE DATA: {license_deactivate_data}')


def run():
    main()


if __name__ == "__main__":
    run()
