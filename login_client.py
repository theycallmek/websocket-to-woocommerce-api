import machineid
from datetime import datetime
import time
import dotenv
import httpx

dotenv.load_dotenv()

USERNAME = 'test1'
PASSWORD = 'swadbotpass123'
# URL = 'https://fastapi-license-server-meh3ibmmpq-uc.a.run.app'
URL = 'http://127.0.0.1:8000'


def get_session_id():
    return f'{machineid.id()}-{str(datetime.now().timestamp()).replace(".", "-")}'


this_session = get_session_id()


def main():
    print('RUNNING MAIN')
    # POST to /login
    with httpx.Client() as client:
        response = client.post(
            url=f'{URL}/login',
            params={'user_login': USERNAME, 'user_pass': PASSWORD},
            timeout=20
        )
    if response.status_code != 200:
        print(f'response.status_code: {response.status_code}')
        print(response.content)
        return False
    token_data = response.json()
    print(f'TOKEN DATA: {token_data}')

    # POST to /license/activate
    params = {'username': token_data['nicename'], 'client_id': token_data['id'], 'token': token_data['token'], 'session_id': this_session}
    with httpx.Client() as client:
        response = client.post(url=f'{URL}/license/activate', params=params, timeout=20)
    if response.status_code != 200:
        print('WRONG STATUS CODE (/license/activate)')
        return False
    license_status_data = response.json()
    if 'error' in license_status_data.keys():
        print(f'LICENSE STATUS DATA ERROR: {license_status_data["error"]}')
        return False
    else:
        print(f'LICENSE STATUS DATA: {license_status_data}')
    r = 10
    for i in range(r):
        print(f'==============\nPASS: {i + 1}/{r}')
        time.sleep(15)
        # POST to /license/status
        with httpx.Client() as client:
            response = client.post(url=f'{URL}/license/status', params=params, timeout=20)
        if response.status_code != 200:
            print('WRONG STATUS CODE (/license/status)')
            return False
        license_status_data = response.json()
        print(f'LICENSE STATUS DATA: {license_status_data}')
        if i >= 9:
            print('DONE!')

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


if __name__ == '__main__':
    run()
