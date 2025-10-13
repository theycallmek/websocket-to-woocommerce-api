import os
import datetime
from aiohttp import web
import socketio
import jwt
import httpx
import aiohttp_jinja2
import jinja2
from dotenv import load_dotenv

colorize_terminal = False
PORT = 8080
SERVER_URL = "0.0.0.0"
sio = socketio.AsyncServer()
app = web.Application()
sio.attach(app)
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader("templates"))
active_sessions = {}
connection_log = []
load_dotenv()


class UserSession:
    def __init__(self, sid, token, username, user_id, api_data, ip):
        self.sid = sid
        self.token = token
        self.username = username
        self.user_id = user_id
        self.product_id = api_data["product_id"]
        self.master_api_key = api_data["master_api_key"]
        self.this_session = api_data["this_session"]
        self.ip = ip

    @staticmethod
    def verify_token(token, remote_ip, sid, username, this_session):
        try:
            payload = jwt.decode(
                jwt=token,
                key=str(os.environ["WP_JWT"]),
                algorithms=["HS256"],
                options={"verify_signature": True},
            )
            # print(f'Payload: {c_grey(payload)}')
            print(
                f"[{UserSession.dt()}]"
                f'{c_purple("<" + remote_ip + ">")} '
                f"{c_cyan(username)} "
                f"{c_blue(sid)} "
                f'{c_green("Token verified. User is authenticated")} Session ID: '
                f"{c_grey(this_session)}"
            )
            return payload
        except jwt.InvalidTokenError as e:
            print(
                f"[{UserSession.dt()}]"
                f'{c_purple("<" + remote_ip + ">")} '
                f"{c_cyan(username)} "
                f"{c_blue(sid)} "
                f'{c_red("Invalid token")}: {c_red(str(e))}'
            )
            return None

    @staticmethod
    def dt():
        return datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]

    def __str__(self):
        return (
            f"'sid': '{self.sid}', 'username': '{self.username}', "
            f"'user_id': '{self.user_id}', 'token': '{self.token}', "
            f"'product_id': '{self.product_id}', "
            f"'master_api_key': '{self.master_api_key}', "
            f"'this_session': '{self.this_session}'"
        )

    def __repr__(self):
        return self.__str__()


async def license_api(action, token, apikey, session_id, product_id):
    # Possible values for action: 'status', 'activate', 'deactivate'
    url = "https://swadbot.com/"
    params = {
        "wc-api": "wc-am-api",
        "wc_am_action": action,
        "api_key": apikey,
        "instance": session_id,
        "product_id": product_id,
    }
    # with httpx.AsyncClient() as client:
    response = await httpx.AsyncClient().post(
        url=url, params=params, headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code == 200:
        json_data = response.json()
        return json_data
    else:
        return None


async def index(request_):
    """Serve the client-side application."""
    return aiohttp_jinja2.render_template(
        "index.html",
        context={
            "active_sessions": active_sessions,
            "session_count": len(active_sessions),
            "connection_log": connection_log,
        },
        request=request_,
    )


@sio.on("connect")
async def connect(sid, environ, auth):
    try:
        remote_ip = auth["ip"]
    except TypeError:
        remote_ip = "0.0.0.0"
    if auth is None:
        print(
            f'[{UserSession.dt()}]{c_purple("<" + remote_ip + ">")} '
            f'{c_cyan(auth["username"])} connected with SID '
            f'{c_blue(sid)} and {c_red("NO token")}'
        )
        await sio.emit("message", f"{remote_ip} {sid}, invalid token.", to=sid)
        await sio.disconnect(sid)
        # await sio.eio.disconnect(sid)
        html_log(
            sid, "connected with no token", ip=remote_ip, username=auth["username"]
        )
        return
    print(
        f"[{UserSession.dt()}]"
        f'{c_purple("<" + remote_ip + ">")} '
        f'{c_cyan(auth["username"])} connected with SID '
        f"{c_blue(sid)} and token: "
        f'{c_grey(auth["token"][:16] + "..." + auth["token"][-43:])}'
    )
    await sio.emit(
        "message", f"Hello {remote_ip} {sid}, we are verifying your token...", to=sid
    )
    result = UserSession.verify_token(
        auth["token"],
        remote_ip,
        sid,
        auth["username"],
        auth["api_data"]["this_session"],
    )
    if result is None:
        await sio.emit("message", f"Invalid token: {result}", to=sid)
        await sio.disconnect(sid)
        html_log(
            sid, "connected with invalid token", ip=remote_ip, username=auth["username"]
        )
    else:
        html_log(
            sid, "connected and authenticated", ip=remote_ip, username=auth["username"]
        )
        active_sessions[sid] = UserSession(
            sid,
            auth["token"],
            auth["username"],
            auth["user_id"],
            auth["api_data"],
            remote_ip,
        )
        license_api_response = await license_api(
            "activate",
            auth["token"],
            auth["api_data"]["master_api_key"],
            auth["api_data"]["this_session"],
            auth["api_data"]["product_id"],
        )
        if license_api_response["success"]:
            print(
                f"[{UserSession.dt()}]"
                f'{c_purple("<" + remote_ip + ">")} '
                f'{c_cyan(auth["username"])} '
                f"{c_blue(sid)} "
                f'{c_green("Node lock acquired. License is activated!")}'
                f'({c_white(license_api_response["message"])})'
            )
            await sio.emit("message", "Success!", to=sid)
        else:
            print(
                f"[{UserSession.dt()}]"
                f'{c_purple("<" + remote_ip + ">")} '
                f'{c_cyan(auth["username"])} '
                f"{c_blue(sid)} "
                f'{c_red("license is not activated.")} '
                f'(Response Code: {c_red(license_api_response["code"])}) '
                f'{license_api_response["error"]}'
            )
            await sio.emit("message", "License is not activated", to=sid)
            await sio.disconnect(sid)
            # await sio.eio.disconnect(sid)


@sio.on("message")
async def message(sid, data):
    print(
        f'[{UserSession.dt()}]{c_purple("<" + active_sessions[sid].ip + ">")} '
        f"{c_cyan(active_sessions[sid].username)} "
        f"{c_blue(sid)}: "
        f"{c_yellow(data)}"
    )
    if data == "poopoo":
        print(f'[{UserSession.dt()}] {c_green("Super secret message received!")} ')
        return
    await sio.emit("message", sid + ": " + data)


@sio.on("disconnect")
async def disconnect(sid):
    if sid not in active_sessions:
        print(
            f"[{UserSession.dt()}]",
            c_yellow(" Session not found. No need to clean dict."),
        )
        return
    session = active_sessions[sid]
    html_log(sid, "disconnected", ip=session.ip, username=session.username)
    license_api_response = await license_api(
        "deactivate",
        session.token,
        session.master_api_key,
        session.this_session,
        session.product_id,
    )
    try:
        msg = (
            f'{c_green("Node lock released successfully!")} '
            f'({license_api_response["activations_remaining"]})'
        )
    except KeyError:
        try:
            msg = (
                f'{c_red("Node lock release failed!")} Code '
                f'{c_red(license_api_response["code"])}. '
                f'{license_api_response["error"]}'
            )
        except KeyError:
            msg = "unknown"
    print(
        f"[{UserSession.dt()}]"
        f'{c_purple("<" + active_sessions[sid].ip + ">")} '
        f"{c_cyan(active_sessions[sid].username)} "
        f"{c_blue(sid)} "
        f'{c_red("Disconnected!")} '
        f"{msg}"
    )
    del active_sessions[sid]
    # await sio.disconnect(sid)
    await sio.eio.disconnect(sid)


@sio.on("heartbeat")
async def heartbeat(sid, data):
    session = active_sessions[sid]
    license_api_response = await license_api(
        "status",
        session.token,
        session.master_api_key,
        session.this_session,
        session.product_id,
    )
    print(
        f'[{UserSession.dt()}]{c_purple("<" + session.ip + ">")} '
        f"{c_cyan(session.username)} "
        f"{c_blue(sid)}: "
        f"{c_yellow(data)}. "
        f'API Response: Node lock is {license_api_response["status_check"]}'
    )
    if license_api_response["status_check"] == "active":
        await sio.emit("heartbeat", "pong", to=sid)
        return
    await sio.emit("heartbeat", "fail", to=sid)
    print(
        f'[{UserSession.dt()}]{c_purple("<" + session.ip + ">")} '
        f"{c_cyan(session.username)} "
        f"{c_blue(sid)} "
        f'{c_red("Node lock is not active.")} Disconnecting...'
    )
    await sio.disconnect(sid)


# Unused
def get_client_ip(environ):
    """
    Doesn't seem to work in local or production, hacky solution for now is to have the
    client send the IP after querying ipify's api. Definitely not the best solution.
    Will need to find a better way.
    """
    if environ.get("HTTP_X_FORWARDED_FOR") is None:
        a = environ["REMOTE_ADDR"]
    else:
        a = environ["HTTP_X_FORWARDED_FOR"]
    print(f"CLIENT IP: {a}")
    return a


def html_log(sid, msg, ip=None, username="Unknown"):
    connection_log.append(f"[{UserSession.dt()}] <{ip}> {username} {sid} {msg}")
    if len(connection_log) > 200:
        connection_log.pop()


app.router.add_static("/static", "static")
app.router.add_get("/", index)


# color console output (windows not supported)
def c_grey(text: str) -> str:
    return f"\033[90m{text}\033[00m" if colorize_terminal else text


def c_red(text: str) -> str:
    return f"\033[91m{text}\033[00m" if colorize_terminal else text


def c_green(text: str) -> str:
    return f"\033[92m{text}\033[00m" if colorize_terminal else text


def c_yellow(text: str) -> str:
    return f"\033[93m{text}\033[00m" if colorize_terminal else text


def c_blue(text: str) -> str:
    return f"\033[94m{text}\033[00m" if colorize_terminal else text


def c_purple(text: str) -> str:
    return f"\033[95m{text}\033[00m" if colorize_terminal else text


def c_cyan(text: str) -> str:
    return f"\033[96m{text}\033[00m" if colorize_terminal else text


def c_white(text: str) -> str:
    return f"\033[97m{text}\033[00m" if colorize_terminal else text


def c_default(text: str) -> str:
    return f"\033[99m{text}\033[00m" if colorize_terminal else text


async def my_web_app():
    print("Starting SWADBot License Server... <3 <3 <3")
    return app


if __name__ == "__main__":
    web.run_app(my_web_app(), host=SERVER_URL, port=PORT)
