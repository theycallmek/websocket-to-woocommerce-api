import asyncio
import socketio
from socketio import exceptions
import httpx
from aioconsole import ainput
import json
import machineid
from datetime import datetime

# PORT = ":8080"
SERVER_URL = 'http://127.0.0.1'
# SERVER_URL = 'http://34.132.62.177/'
# SERVER_URL = "http://34.132.72.199/"

PORT = "8000"

sio = socketio.AsyncClient()
LIC_SESSION_ID = ""
HEARTBEAT_ENABLED = False
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@sio.on("connect")
async def connect():
    print("Connection established with transport:", sio.transport())
    await sio.emit("message", "Hello from client")


@sio.on("message")
async def message(data):
    if data == "License is not activated":
        await sio.disconnect()
        print("License is not activated")
    if ", invalid token." in data:
        await sio.disconnect()
        print("Invalid token")
    print(f"[{SERVER_URL}:{PORT}]: {data}")


@sio.on("disconnect")
async def disconnect():
    print("disconnected from server")
    await sio.eio.disconnect()


@sio.on("heartbeat")
async def on_heartbeat(data):
    print("Heartbeat received: ", data)
    if "fail" in data:
        await sio.disconnect()
        print("Heartbeat failed")
        await sio.eio.disconnect()


async def heartbeat():
    while HEARTBEAT_ENABLED:
        print("Sending heartbeat...")
        await sio.emit("heartbeat", "ping")
        await asyncio.sleep(30)
    return


async def send_message():
    count = 0
    while True:
        a = await ainput(f"[{count}] Send a message: \n")
        count += 1
        if a == "exit":
            await sio.disconnect()
            return
        await sio.send(a)
        await asyncio.sleep(0.1)


async def get_my_ip():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.ipify.org")
    if response.status_code == 200:
        return response.text
    return "0.0.0.0"


async def get_token(username, password):
    auth_endpoint = "https://swadbot.com/wp-json/jwt-auth/v1/token"
    payload = {"username": username, "password": password}
    # Send the POST request and store the response
    async with httpx.AsyncClient() as client:
        response = await client.post(auth_endpoint, json=payload)
    my_ip = await get_my_ip()
    print(f"MY IP: {my_ip}")
    # Check the status code of the response
    if response.status_code == 200:
        # If the request was successful, the JWT token will be in the response data
        token = str(response.json()["data"]["token"])
        user_id = response.json()["data"]["id"]
        api_data = await get_api_data(user_id, token)
        if api_data is None:
            return None
        api_data["this_session"] = get_session_id()
        return {
            "token": token,
            "user_id": user_id,
            "username": username,
            "api_data": api_data,
            "ip": my_ip,
        }
    if response.status_code == 403:
        print(f'Error: {response.json()["message"]}')
        return None
    print(f"JSON:\n{response.json()}")
    # If the request was not successful, print the error message
    print(f'Error: {response.json()["message"]}')
    return None


async def get_api_data(user_id, token):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://swadbot.com/wp-json/sw/v1/apikey",
            params={"id": f"{user_id}"},
            headers={"Authorization": f"Bearer {token}"},  # DEBUG
        )
    if response.status_code != 200:
        print(f'Error retrieving API data: {response.json()["message"]}')
        return None
    json_data = response.json()
    print(f"API DATA: {json_data}")
    if "no_sub" in json_data:
        return "no_sub"
    if "current_dt" not in json_data:
        return None
    # Converts string from server to python dict
    return json.loads("{" + json_data + "}")


def get_session_id():
    global LIC_SESSION_ID
    # Only generate a new session ID on first pass. Use constant on subsequent passes.
    if LIC_SESSION_ID == "":
        session_id = (
            f'{machineid.id()}-{str(datetime.now().timestamp()).replace(".", "-")}'
        )
        LIC_SESSION_ID = session_id
    else:
        session_id = LIC_SESSION_ID
    # print(f'SESSION ID: {session_id}')
    return session_id


async def main():
    token = await get_token("test1", "swadbotpass123")
    if token is None:
        print("Error getting token. Quitting...")
        return
    try:
        await sio.connect(f"{SERVER_URL}{PORT}", auth=token)
        tasks = [
            asyncio.create_task(heartbeat()),
        ]
        await asyncio.gather(*tasks)
        await sio.wait()
    except exceptions.ConnectionError as e:
        print("Error:", e)


def run_auth():
    asyncio.run(main())


if __name__ == "__main__":
    run_auth()
