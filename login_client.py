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
    """Generates a unique session ID for the client.

    The session ID is a combination of the machine's unique ID and the
    current timestamp.

    Returns:
        str: A unique session identifier string.
    """
    return f'{machineid.id()}-{str(datetime.now().timestamp()).replace(".", "-")}'


def get_my_ip():
    """Retrieves the public IP address of the client.

    Uses an external service (api.ipify.org) to determine the public IP.

    Returns:
        str: The public IP address as a string, or "0.0.0.0" if the request fails.
    """
    with httpx.Client() as client:
        response = client.get("https://api.ipify.org")
    if response.status_code == 200:
        return response.text
    return "0.0.0.0"


this_session = get_session_id()
client_ip = get_my_ip()

def main():
    """The main function for the license client.

    This function performs the following steps:
    1. Logs into the server using predefined credentials.
    2. Activates a license using the token received from login.
    3. Periodically checks the status of the license.
    4. (Commented out) Deactivates the license.

    Returns:
        bool: False if any step of the process fails, otherwise does not
              explicitly return True but will complete execution.
    """
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
    """Runs the main client logic.

    This is the entry point when the script is executed.
    """
    main()


if __name__ == "__main__":
    run()