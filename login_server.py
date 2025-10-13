import asyncio
import os
import platform
from datetime import datetime, timedelta
from typing import Optional
# import mysql.connector
import logging
import hmac
import hashlib
import base64
import bcrypt
import dotenv
import httpx, typing
from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from passlib.hash import phpass
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.engine import Engine
from sqlmodel import (
    Field,
    Session,
    SQLModel,
    create_engine,
    select,
    update,
    func,
    delete,
)
from sqlmodel.ext.asyncio.session import AsyncSession

dotenv.load_dotenv()
WP_MYSQL_USER = os.environ["WP_MYSQL_USER"]
WP_MYSQL_PASS = os.environ["WP_MYSQL_PASS"]
WP_MYSQL_HOST = os.environ["WP_MYSQL_HOST"]
WP_MYSQL_PORT = os.environ["WP_MYSQL_PORT"]
WP_MYSQL_DB_NAME = os.environ["WP_MYSQL_DB_NAME"]
WP_URI =f'mysql+mysqlconnector://{WP_MYSQL_USER}:{WP_MYSQL_PASS}@{WP_MYSQL_HOST}:{WP_MYSQL_PORT}/{WP_MYSQL_DB_NAME}'
SQLITE_URI = "sqlite+aiosqlite:///database.db"
HEARTBEAT_INTERVAL = int(os.environ["HEARTBEAT_INTERVAL"])
RATE_LIMIT_SECONDS= int(os.environ["RATE_LIMIT_SECONDS"])
# print(f'WP_URI: {WP_URI}\nSQLITE_URI: {SQLITE_URI}\nStarting server with heartbeat interval of '
#       f'{HEARTBEAT_INTERVAL} and rate limit of {RATE_LIMIT_SECONDS} seconds.')
print(
      f'WP_URI: {WP_URI}\n'
      f'SQLITE_URI: {SQLITE_URI}\n'
      f'Hearbeat Interval: {HEARTBEAT_INTERVAL} seconds\n'
      f'Rate Limit: {RATE_LIMIT_SECONDS} seconds\n'
)


def get_wp_mysql_engine() -> Engine:
    return create_engine(url=WP_URI, echo=False)


def get_sqlite_engine() -> AsyncEngine:
    return create_async_engine(url=SQLITE_URI, echo=False)


wp_engine = get_wp_mysql_engine()  # Connects to WordPress MySQL
sqlite_engine = get_sqlite_engine()  # Connects to dedicated SQLite


# --- Rate Limiting Globals ---
login_attempts = {}
LOGIN_ATTEMPTS_LIMIT = 5
LOGIN_ATTEMPTS_WINDOW = timedelta(minutes=1)


def get_my_ip():
    with httpx.Client() as client:
        response = client.get("https://api.ipify.org", timeout=5)
        response = client.get("https://api.ipify.org", timeout=5)
    if response.status_code == 200:
        return response.text
    return "0.0.0.0"


class WPUsers(SQLModel, table=True):
    __tablename__: str = "wp_users"
    ID: int = Field(primary_key=True)
    user_login: str = Field(index=True)
    user_pass: str
    user_nicename: str = Field(index=True)
    user_email: str = Field(index=True)
    user_url: str
    user_registered: datetime
    user_activation_key: str
    user_status: int
    display_name: str


class WPWCAMApiActivation(SQLModel, table=True):
    __tablename__: str = "wp_wc_am_api_activation"
    activation_id: int = Field(primary_key=True, index=True)
    activation_time: datetime
    api_key: str = Field(index=True)
    api_resource_id: int
    assigned_product_id: int
    associated_api_key_id: int
    instance: str = Field(index=True)
    ip_address: str
    master_api_key: str = Field(index=True)
    object: str
    order_id: int
    order_item_id: int
    product_id: str
    product_order_api_key: str
    sub_id: int
    sub_item_id: int
    sub_parent_id: int
    version: str
    update_requests: int
    user_id: int = Field(index=True)


class WPWCAMApiResource(SQLModel, table=True):
    __tablename__: str = "wp_wc_am_api_resource"
    api_resource_id: int = Field(primary_key=True, index=True)
    activation_ids: str
    activations_total: int
    activations_purchased: int
    activations_purchased_total: int
    active: int
    access_expires: datetime
    access_granted: datetime
    associated_api_key_ids: str
    collaborators: str
    download_requests: int
    item_qty: int
    master_api_key: str = Field(index=True)
    order_id: int = Field(index=True)
    order_item_id: int
    order_key: str = Field(index=True)
    parent_id: int
    product_id: int = Field(index=True)
    product_order_api_key: str = Field(index=True)
    product_title: str
    refund_qty: int
    sub_id: int
    sub_item_id: int
    sub_previous_order_id: int
    sub_order_key: str
    sub_parent_id: int
    user_id: int = Field(index=True)
    variation_id: int


class UserSession(SQLModel, table=True):
    __tablename__: str = "user_sessions"
    id: Optional[int] = Field(default=None, primary_key=True)
    token: str
    username: str
    user_id: int
    product_id: int
    master_api_key: str
    this_session: str = Field(index=True)
    ip: Optional[str] = Field(default="0.0.0.0")
    create_date: Optional[datetime] = Field(default_factory=datetime.now)
    last_access: Optional[datetime] = Field(default_factory=datetime.now, index=True)


class TokenData(SQLModel):
    token: str
    user_id: int
    user_email: str
    user_nicename: str
    user_display_name: str


class LicenseResponse(SQLModel):
    success: bool
    message: str
    total_activations: int
    activations_remaining: int


class Logs(SQLModel, table=True):
    __tablename__: str = "logs"
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    ip: str
    message: str
    create_date: Optional[datetime] = Field(default_factory=datetime.now, index=True)

async def create_log_entry(username: str, ip: str, message: str):
    """Creates a log entry and saves it to the database asynchronously."""
    log_entry = Logs(username=username, ip=ip, message=message)
    async with AsyncSession(sqlite_engine) as session:
        session.add(log_entry)
        await session.commit()


def get_wp_user_data(username: str) -> WPUsers:
    with Session(wp_engine) as session:
        # If user enters email as username then use email to find user
        if "@" in username and "." in username:
            statement = select(WPUsers).where(WPUsers.user_email == username)
        else:
            statement = select(WPUsers).where(WPUsers.user_login == username)
        results = session.exec(statement).first()
        return results


async def get_token_data(username: str, password: str) -> dict | None:
    # auth_endpoint = "https://swadbot.com/wp-json/jwt-auth/v1/token"
    auth_endpoint = "https://swadbot.com/wp-json/jwt-auth/v1/token"

    payload = {"username": username, "password": password}
    async with httpx.AsyncClient() as client:
        response = await client.post(auth_endpoint, json=payload, timeout=10)
    if response.status_code == 200:
        logging.debug(f'TOKEN DATA: {response.json()}')
        return response.json()
    elif response.status_code == 403:
        logging.debug(f'Error 403: {response.json()["message"]}')
        return None
    else:
        logging.debug(f'Error: {response.json()["message"]}')
        return None


def verify_pw_hash(pw: str, pw_hash: str) -> bool:
    """
    Verifies a plaintext password against a modern WordPress hash
    that starts with '$wp'.
    """
    if not isinstance(pw_hash, str) or not pw_hash.startswith('$wp$'):
        # This function is only for modern WordPress hashes.
        return False

    if len(pw) > 4096:
        return False

    # The bcrypt library expects the hash without the '$wp$' prefix.
    # It also requires both the password and hash to be bytes.
    password_bytes = pw.encode('utf-8')
    logging.debug(f"pw_hash: {pw_hash}")
    bcrypt_hash_bytes = pw_hash[3:].encode('utf-8')

    # Step 1: For modern '$wp$' hashes, WordPress first pre-hashes the password
    # using HMAC-SHA384 before passing it to bcrypt. We must replicate this.
    password_to_verify = base64.b64encode(
        hmac.new(
            b'wp-sha384',
            password_bytes,
            hashlib.sha384
        ).digest()
    )

    # Step 2: Use bcrypt's checkpw to securely compare the pre-hashed password
    # with the bcrypt portion of the database hash.
    return bcrypt.checkpw(password_to_verify, bcrypt_hash_bytes)


app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static", html=True), name="static")


async def create_db_and_tables():
    async with sqlite_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


@app.on_event("startup")
async def startup():
    logging.debug("STARTING UP")
    await create_db_and_tables()
    asyncio.create_task(deactivate_expired_sessions())


@app.get("/admin/{password}", response_class=HTMLResponse)
async def admin(request: Request, password: str):
    try:
        client_ip = request.headers["X-Forwarded-For"]
    except KeyError:
        client_ip = request.client.host

    # --- Rate Limiting Logic for Admin Page ---
    now = datetime.now()
    if client_ip in login_attempts:
        attempt_info = login_attempts[client_ip]
        if now - attempt_info["window_start"] > LOGIN_ATTEMPTS_WINDOW:
            login_attempts[client_ip] = {"count": 1, "window_start": now}
        elif attempt_info["count"] >= LOGIN_ATTEMPTS_LIMIT:
            await create_log_entry(username="admin_login", ip=client_ip, message="Admin login failed: Rate limit exceeded.")
            return templates.TemplateResponse(
                "index.html",
                {"request": request, "client_ip": client_ip, "error_message": "Too many attempts. Please wait a minute."},
            )
        else:
            attempt_info["count"] += 1
    else:
        login_attempts[client_ip] = {"count": 1, "window_start": now}
    # --- End Rate Limiting Logic ---

    if password == "password": # Replace "password" with a secure value in production
        if client_ip in login_attempts:
            del login_attempts[client_ip] # Clear attempts on success
        active_users = await get_active_users()
        logs = await get_logs_from_db(100)
        return templates.TemplateResponse(
            "admin.html",
            {"request": request, "active_users": active_users, "logs": logs},
        )
    else:
        # On failure, construct the error message with the attempt count
        attempts_made = login_attempts.get(client_ip, {}).get("count", 1)
        remaining = LOGIN_ATTEMPTS_LIMIT - attempts_made
        error_msg = f"Incorrect password. {remaining} attempts remaining."
        await create_log_entry(username="admin_login", ip=client_ip, message="Admin login failed: Incorrect password.")
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "client_ip": client_ip, "error_message": error_msg},
        )

@app.get("/admin/api/data/{password}", response_class=JSONResponse)
async def admin_data(password: str):
    """API endpoint to fetch dynamic admin data."""
    if password == "password":
        active_users = await get_active_users()
        augmented_users = []
        for user in active_users:
            # Get total allowed activations from WordPress DB
            api_data = await get_wp_api_resource_data(user.user_id)
            total_activations = api_data.activations_purchased if api_data else 0

            # Get currently used activations from local DB
            currently_active = await count_active_sessions_for_user(user.user_id)

            # Convert the SQLModel object to a dict and add the new fields
            user_dict = user.dict()
            user_dict["total_activations"] = total_activations
            user_dict["activations_remaining"] = total_activations - currently_active
            augmented_users.append(user_dict)

        logs = await get_logs_from_db(100)
        # FastAPI will automatically serialize the SQLModel objects to JSON
        return {"active_users": augmented_users, "logs": logs}
    else:
        return JSONResponse(status_code=401, content={"message": "Unauthorized"})

class DeactivateRequest(SQLModel):
    password: str

@app.post("/admin/api/deactivate/{session_id}")
async def deactivate_session_admin(session_id: str, payload: DeactivateRequest):
    """Allows an admin to manually deactivate a specific session."""
    if payload.password != "password":
        return JSONResponse(status_code=401, content={"message": "Unauthorized"})

    # Find the session by its unique string ID ('this_session'), not the integer primary key ('id')
    async with AsyncSession(sqlite_engine) as session:
        statement = select(UserSession).where(UserSession.this_session == session_id)
        client_session = (await session.execute(statement)).scalar_one_or_none()

    if not client_session:
        return JSONResponse(status_code=404, content={"message": "Session not found"})

    # Create a specific log entry for the admin action before deactivating.
    await create_log_entry(
        username=client_session.username,
        ip="admin",  # Or get admin IP from request if you add it
        message=f"Session [{session_id}] deactivated by admin.",
    )
    await license_api(
        request=None,  # Internal call
        action="deactivate",
        username=client_session.username,
        client_id=client_session.user_id,
        token=client_session.token,
        session_id=client_session.this_session,
    )
    return JSONResponse(status_code=200, content={"message": "Session deactivated successfully"})

@app.get("/")
async def root(request: Request):
    logging.debug("ROOT")
    try:
        client_ip = request.headers["X-Forwarded-For"]
        logging.debug(f"client ip={client_ip}")
    except KeyError:
        client_ip = request.client.host
        logging.debug(f"Caught KeyError: client ip={client_ip}")
    # return {"message": "Welcome sensei!", "ip": client_ip}
    return templates.TemplateResponse(
        "index.html",
        {"request": request, 'client_ip': client_ip},
    )


@app.post("/login", response_model=TokenData)
async def login(
    request: Request, user_login: str, user_pass: str
) -> dict | JSONResponse:
    logging.debug("LOGIN")
    try:
        client_ip = request.headers["X-Forwarded-For"]
    except KeyError:
        client_ip = request.client.host

    # --- Rate Limiting Logic ---
    now = datetime.now()
    if client_ip in login_attempts:
        attempt_info = login_attempts[client_ip]
        # If the time window has passed, reset the attempts for this IP
        if now - attempt_info["window_start"] > LOGIN_ATTEMPTS_WINDOW:
            login_attempts[client_ip] = {"count": 1, "window_start": now}
        # If attempts are exceeded within the window, block the request
        elif attempt_info["count"] >= LOGIN_ATTEMPTS_LIMIT:
            await create_log_entry(username=user_login, ip=client_ip, message="Login failed: Rate limit exceeded.")
            return JSONResponse(
                status_code=429,
                content={"message": "Too many login attempts. Please wait a minute and try again."}
            )
        else:
            # Otherwise, just increment the attempt count
            attempt_info["count"] += 1
    else:
        # This is the first attempt from this IP in a while
        login_attempts[client_ip] = {"count": 1, "window_start": now}
    # --- End Rate Limiting Logic ---

    data = get_wp_user_data(user_login)
    try:
        logging.debug(f"HASH FROM DB: {data.user_pass}")
        verified = verify_pw_hash(user_pass, data.user_pass)
    except AttributeError as e:
        logging.debug(f"CAUGHT ATTRIBUTE ERROR: {e}")
        verified = False
    if verified:
        token_data = await get_token_data(user_login, user_pass)
        if token_data:
            # On successful login, clear the rate limit counter for this IP
            if client_ip in login_attempts:
                del login_attempts[client_ip]
            # Construct the response object to match the TokenData model
            response_data = TokenData(
                token=token_data["token"],
                user_id=data.ID,  # Get the ID from the database user object
                user_email=token_data["user_email"],
                user_nicename=token_data["user_nicename"],
                user_display_name=token_data["user_display_name"],
            )
            # await create_log_entry(username=user_login, ip=client_ip, message="Login successful!")
            return response_data

    # This block is reached if verification fails or if token fetching fails
    await create_log_entry(username=user_login, ip=client_ip, message="Login failed!")
    return JSONResponse(status_code=401, content={"message": "Login failed"})

async def get_request_or_none(request: Request) -> typing.Optional[Request]:
    return request

@app.post("/license/{action}")
async def license_api(
    action: str,
    username: str,
    client_id: int,
    token: str,
    session_id: str,
    # Use Depends to correctly handle the optional Request dependency
    request: typing.Optional[Request] = Depends(get_request_or_none),
) -> LicenseResponse | None:
    # Possible values for action: 'status', 'activate', 'deactivate'
    if request is not None:
        # Called from a user request, get IP from headers
        try:
            client_ip = request.headers["X-Forwarded-For"]
        except KeyError:
            client_ip = request.client.host
    else:
        # Called internally from timeout or admin deactivate, get IP from the stored session
        async with AsyncSession(sqlite_engine) as session:
            # This query was incorrect, it should use scalar_one_or_none
            db_session = (await session.execute(select(UserSession).where(UserSession.this_session == session_id))).scalar_one_or_none()
            client_ip = db_session.ip if db_session else "unknown"

    # Get license data from WordPress early for all actions
    api_data = await get_wp_api_resource_data(client_id)

    if action == "activate":
        if not await check_last_create_date(client_id):
            await create_log_entry(
                username=username,
                ip=client_ip,
                message="Activation failed! Rate-limit exceeded.",
            )
            return LicenseResponse(
                success=False,
                message="Rate-limit exceeded. Slow down, sensei.",
                total_activations=0,
                activations_remaining=0,
            )

        # NEW LOGIC: Check floating license count against the local database
        if not api_data:
            return LicenseResponse(success=False, message="No license resource found for user.", total_activations=0, activations_remaining=0)

        total_allowed_activations = api_data.activations_purchased
        currently_active_sessions = await count_active_sessions_for_user(client_id)

        if currently_active_sessions >= total_allowed_activations:
            await create_log_entry(
                username=username,
                ip=client_ip,
                message="Activation failed! Maximum number of active sessions reached.",
            )
            return LicenseResponse(
                success=False,
                message="Maximum number of active sessions reached.",
                total_activations=total_allowed_activations,
                activations_remaining=0,
            )

    url = "https://swadbot.com/"
    # logging.debug(f'API_DATA: {api_data}')
    try:
        prod_id = api_data.product_id
    except KeyError:
        Logs(
            username=username,
            ip=client_ip,
            message=f"Attemted action {action} failed! No active license found for this user.",
        )
        return LicenseResponse(
            success=False,
            message="No active license found for this user.",
            total_activations=0,
            activations_remaining=0,
        )
    client_session = UserSession(
        token=token,
        username=username,
        user_id=client_id,
        product_id=prod_id,
        master_api_key=api_data.master_api_key,
        this_session=session_id,
        ip=client_ip,
        create_date=datetime.now(),
        last_access=datetime.now(),
    )

    if action == "activate":
        await client_session_write(client_session)
    elif action == "status":
        # For a status check (heartbeat), we only need to update our local session.
        # We don't need to call the external WooCommerce API, as that would be redundant
        # and can return misleading "inactive" statuses.

        # CRITICAL FIX: First, verify the session actually exists in our database.
        async with AsyncSession(sqlite_engine) as session:
            statement = select(UserSession).where(UserSession.this_session == client_session.this_session)
            existing_session = (await session.execute(statement)).scalar_one_or_none()

        if not existing_session:
            await create_log_entry(username=username, ip=client_ip, message="Heartbeat failed: Session not found.")
            return LicenseResponse(
                success=False,
                message="Session not found or has been deactivated.",
                total_activations=0,
                activations_remaining=0,
            )

        await client_session_update(client_session) # Update the timestamp

        # Calculate the correct floating license count for the status response
        total_allowed = api_data.activations_purchased if api_data else 0
        currently_active = await count_active_sessions_for_user(client_id)

        return LicenseResponse(
            success=True,
            message="Session heartbeat updated.",
            total_activations=total_allowed,
            activations_remaining=total_allowed - currently_active,
        )
    elif action == "deactivate":
        pass # Deletion will happen after the external API call.

    ar = LicenseResponse(
        success=True, message="", total_activations=0, activations_remaining=0
    )
    if action == "activate":
        # For a floating license, a successful internal check is all that's needed.
        # We no longer need to check the response from the external API.
        ar.success = True
        ar.total_activations = api_data.activations_purchased
        # The new remaining count is total minus the sessions that are now active (including this new one)
        ar.activations_remaining = api_data.activations_purchased - (await count_active_sessions_for_user(client_id))
        ar.message = f"Activation successful. {ar.activations_remaining} of {ar.total_activations} floating licenses remaining."
        log_message = f"Session [{session_id}] activated by user. {ar.activations_remaining}/{ar.total_activations} remaining."
        await create_log_entry(username=username, ip=client_ip, message=log_message)
    elif action == "deactivate":
        # Check if the request came from the timeout function (no request object) or a user
        # Admin deactivations are logged in their own endpoint, so `request is None` here always means a timeout.
        log_message = f"Session [{session_id}] deactivated due to timeout." if request is None \
            else f"Session [{session_id}] deactivated by user."
        await create_log_entry(username=username, ip=client_ip, message=log_message)
        # Now that all operations are complete, delete the session from the local DB.
        await client_session_delete(client_session)

    return ar


async def deactivate_expired_sessions() -> None:
    while True:
        async with AsyncSession(sqlite_engine) as session:
            statement = select(UserSession).where(
                UserSession.last_access < datetime.now() - timedelta(seconds=10)
            )
            results = await session.execute(statement)
            for client_session in results.scalars():
                # Re-instating the call to license_api is crucial. It handles both
                # the external API call and the local database cleanup.
                await license_api(
                    request=None,  # Pass None to indicate an internal/timeout call
                    action="deactivate",
                    username=client_session.username,
                    client_id=client_session.user_id,
                    token=client_session.token,
                    session_id=client_session.this_session,
                )
                logging.debug(f"DEACTIVATED SESSION: {client_session}")
        await asyncio.sleep(HEARTBEAT_INTERVAL)


async def client_session_delete(client_session: UserSession) -> None:
    async with AsyncSession(sqlite_engine) as session:
        statement = delete(UserSession).where(
            UserSession.this_session == client_session.this_session
        )
        await session.execute(statement)
        await session.commit()
    logging.debug(f'DELETED SESSION FROM DB: {client_session}')


async def client_session_update(client_session: UserSession) -> None:
    async with AsyncSession(sqlite_engine) as session:
        statement = (
            update(UserSession)
            .where(UserSession.this_session == client_session.this_session)
            .values(last_access=datetime.now())
        )
        await session.execute(statement)
        await session.commit()
    logging.debug(f'UPDATED SESSION IN DB: {client_session}')


async def client_session_write(client_session: UserSession) -> None:
    async with AsyncSession(sqlite_engine) as session:
        session.add(client_session)
        await session.commit()
        await session.refresh(client_session)
    logging.debug(f'WROTE SESSION TO DB: {client_session}')


async def get_wp_api_resource_data(user_id: int) -> WPWCAMApiResource:
    with Session(wp_engine) as session:
        statement = select(WPWCAMApiResource).where(
            WPWCAMApiResource.user_id == user_id
        )
        results = session.exec(statement).first()
    logging.debug(f'F_RESULTS: {results}')
    return results


async def get_wp_api_activations_data(
    activation_ids: list[int],
) -> list[WPWCAMApiActivation]:
    with Session(wp_engine) as session:
        total_results = []
        for client_id in activation_ids:
            statement = select(WPWCAMApiActivation).where(
                WPWCAMApiActivation.activation_id == client_id
            )
            results = session.exec(statement).first()
            total_results.append(results)
    logging.debug(f'TOTAL_RESULTS: {total_results}')
    return total_results


async def check_last_create_date(client_id: int) -> bool:
    async with AsyncSession(sqlite_engine) as session:
        statement = (
            select(UserSession)
            .where(UserSession.user_id == client_id)
            .where(UserSession.create_date > datetime.now() - timedelta(seconds=RATE_LIMIT_SECONDS))
        )
        results = await session.execute(statement)
        for _ in results.scalars():
            return False
    return True


async def get_active_users() -> list[UserSession]:
    async with AsyncSession(sqlite_engine) as session:
        statement = select(UserSession)
        results = await session.execute(statement)
        final_list = []
        for client_session in results.scalars():
            final_list.append(client_session)
        return final_list


async def get_logs_from_db(limit: int) -> list[Logs]:
    async with AsyncSession(sqlite_engine) as session:
        statement = select(Logs).order_by(Logs.create_date.desc()).limit(limit)
        results = await session.execute(statement)
        final_list = []
        for log in results.scalars():
            final_list.append(log)
        return final_list

async def count_active_sessions_for_user(user_id: int) -> int:
    """Counts the number of active sessions for a specific user in the local DB."""
    async with AsyncSession(sqlite_engine) as session:
        statement = select(func.count(UserSession.id)).where(UserSession.user_id == user_id)
        count = (await session.execute(statement)).scalar_one()
        return count


def run():
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def test_get_token_data(username: str, password: str) -> dict | None:
    # auth_endpoint = "https://swadbot.com/wp-json/jwt-auth/v1/token"
    auth_endpoint = "https://swadbot.com/wp-json/jwt-auth/v1/token"

    payload = {"username": username, "password": password}
    with httpx.Client() as client:
        response = client.post(auth_endpoint, json=payload, timeout=10)
    if response.status_code == 200:
        logging.debug(f'TOKEN DATA: {response.json()}')
        return response.json()
    elif response.status_code == 403:
        logging.debug(f'Error 403: {response.json()["message"]}')
        return None
    else:
        logging.debug(f'Error: {response.json()["message"]}')
        return None

def login_test(user_login: str, user_pass: str) -> dict | JSONResponse:
    logging.debug("LOGIN")
    data = get_wp_user_data(user_login)
    client_ip = '127.0.0.1'
    try:
        verified = verify_pw_hash(user_pass, data.user_pass)
    except AttributeError as e:
        logging.debug(f"CAUGHT ATTRIBUTE ERROR: {e}")
        verified = False
    if verified:
        token_data = test_get_token_data(user_login, user_pass)
        Logs(username=user_login, ip=client_ip, message="Login successful!")
    else:
        Logs(username=user_login, ip=client_ip, message="Login failed!")
        return JSONResponse(status_code=401, content={"message": "Login failed"})
    return token_data

if __name__ == "__main__":
    USERNAME = 'test1'
    PASSWORD = 'swadbotpass123'

    print("name = __main__")
    login_test(USERNAME, PASSWORD)

else: # NOT EQUALS to run when ran through uvicorn etc
    print("name != __main__")
    run()
