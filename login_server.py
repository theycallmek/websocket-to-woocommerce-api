import asyncio
import os
import platform
import json
from passlib.hash import phpass
from datetime import datetime, timedelta
from typing import Optional
from sqlmodel import Field, Session, SQLModel, engine, create_engine, select, update, delete
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import httpx
import dotenv

dotenv.load_dotenv()
WP_URI = (
    f'mysql+pymysql://{os.environ["WP_MYSQL_USER"]}'
    f':{os.environ["WP_MYSQL_PASS"]}'
    f'@{os.environ["WP_MYSQL_HOST"]}'
    f':{os.environ["WP_MYSQL_PORT"]}'
    f'/{os.environ["WP_MYSQL_DB_NAME"]}'
)
PG_URI = (
    f'postgresql+asyncpg://{os.environ["PG_USER"]}'
    f':{os.environ["PG_PASSWORD"]}'
    f'@{os.environ["PG_HOST"]}'
    f'/{os.environ["PG_DB_NAME"]}'
)


def get_wp_mysql_engine() -> engine:
    """Creates and returns a SQLAlchemy engine for the WordPress MySQL database.

    Returns:
        sqlalchemy.engine.Engine: The SQLAlchemy engine instance.
    """
    return create_engine(
        url=WP_URI,
        echo=False
    )


def get_pg_engine() -> AsyncEngine:
    """Creates and returns an async SQLAlchemy engine for the PostgreSQL database.

    Returns:
        sqlalchemy.ext.asyncio.AsyncEngine: The async SQLAlchemy engine instance.
    """
    return create_async_engine(url=PG_URI, echo=False)


wp_engine = get_wp_mysql_engine()  # Connects to WordPress MySQL
pg_engine = get_pg_engine()  # Connects to dedicated PostgresSQL


def get_my_ip():
    """Retrieves the public IP address of the server.

    Returns:
        str: The public IP address, or '0.0.0.0' if the request fails.
    """
    with httpx.Client() as client:
        response = client.get('https://api.ipify.org', timeout=5)
    if response.status_code == 200:
        return response.text
    return '0.0.0.0'


class WPUsers(SQLModel, table=True):
    """
    SQLModel for the `wp_users` table.

    Attributes:
        ID (int): Primary key.
        user_login (str): User's login name.
        user_pass (str): Hashed password.
        user_nicename (str): User's nice name for URLs.
        user_email (str): User's email address.
        user_url (str): User's website URL.
        user_registered (datetime): Date and time of registration.
        user_activation_key (str): Activation key for registration.
        user_status (int): User's status.
        display_name (str): User's display name.
    """
    __tablename__: str = 'wp_users'
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
    """
    SQLModel for the `wp_wc_am_api_activation` table.

    Attributes:
        activation_id (int): Primary key.
        activation_time (datetime): Time of activation.
        api_key (str): API key used for activation.
        api_resource_id (int): ID of the API resource.
        assigned_product_id (int): ID of the assigned product.
        associated_api_key_id (int): ID of the associated API key.
        instance (str): Unique instance ID for the activation.
        ip_address (str): IP address of the client.
        master_api_key (str): Master API key.
        object (str): Object type.
        order_id (int): Order ID.
        order_item_id (int): Order item ID.
        product_id (str): Product ID.
        product_order_api_key (str): Product order API key.
        sub_id (int): Subscription ID.
        sub_item_id (int): Subscription item ID.
        sub_parent_id (int): Subscription parent ID.
        version (str): Software version.
        update_requests (int): Number of update requests.
        user_id (int): User ID.
    """
    __tablename__: str = 'wp_wc_am_api_activation'
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
    """
    SQLModel for the `wp_wc_am_api_resource` table.

    Attributes:
        api_resource_id (int): Primary key.
        activation_ids (str): Comma-separated list of activation IDs.
        activations_total (int): Total number of activations.
        activations_purchased (int): Number of purchased activations.
        activations_purchased_total (int): Total number of purchased activations.
        active (int): Whether the resource is active.
        access_expires (datetime): Date and time when access expires.
        access_granted (datetime): Date and time when access was granted.
        associated_api_key_ids (str): Comma-separated list of associated API key IDs.
        collaborators (str): Collaborators.
        download_requests (int): Number of download requests.
        item_qty (int): Item quantity.
        master_api_key (str): Master API key.
        order_id (int): Order ID.
        order_item_id (int): Order item ID.
        order_key (str): Order key.
        parent_id (int): Parent ID.
        product_id (int): Product ID.
        product_order_api_key (str): Product order API key.
        product_title (str): Product title.
        refund_qty (int): Refund quantity.
        sub_id (int): Subscription ID.
        sub_item_id (int): Subscription item ID.
        sub_previous_order_id (int): Previous subscription order ID.
        sub_order_key (str): Subscription order key.
        sub_parent_id (int): Subscription parent ID.
        user_id (int): User ID.
        variation_id (int): Variation ID.
    """
    __tablename__: str = 'wp_wc_am_api_resource'
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
    """
    SQLModel for the `user_sessions` table.

    Attributes:
        id (Optional[int]): Primary key.
        token (str): JWT token for the session.
        username (str): User's login name.
        user_id (int): User's ID.
        product_id (int): ID of the product being accessed.
        master_api_key (str): Master API key for the product.
        this_session (str): Unique session ID.
        ip (Optional[str]): IP address of the client.
        create_date (Optional[datetime]): Timestamp of session creation.
        last_access (Optional[datetime]): Timestamp of the last access.
    """
    __tablename__: str = 'user_sessions'
    id: Optional[int] = Field(default=None, primary_key=True)
    token: str
    username: str
    user_id: int
    product_id: int
    master_api_key: str
    this_session: str = Field(index=True)
    ip: Optional[str] = Field(default='0')
    create_date: Optional[datetime] = Field(default=datetime.now())
    last_access: Optional[datetime] = Field(default=datetime.now(), index=True)


class TokenData(SQLModel):
    """Pydantic model for the token data response."""
    token: str
    id: int
    email: str
    nicename: str
    firstName: str
    lastName: str
    displayName: str


class LicenseResponse(SQLModel):
    """Pydantic model for the license API response."""
    success: bool
    message: str
    total_activations: int
    activations_remaining: int


def get_wp_user_data(username: str) -> WPUsers:
    """Retrieves a user's data from the WordPress database.

    Args:
        username: The user's login name or email address.

    Returns:
        WPUsers: A WPUsers object containing the user's data, or None if not found.
    """
    with Session(wp_engine) as session:
        # If user enters email as username then use email to find user
        if '@' in username and '.' in username:
            statement = select(WPUsers).where(WPUsers.user_email == username)
        else:
            statement = select(WPUsers).where(WPUsers.user_login == username)
        results = session.exec(statement).first()
        return results


async def get_token_data(username: str, password: str) -> dict | None:
    """Authenticates with WordPress and retrieves a JWT token.

    Args:
        username: The user's login name.
        password: The user's password.

    Returns:
        dict | None: A dictionary containing the token data if successful, otherwise None.
    """
    auth_endpoint = 'https://swadbot.com/wp-json/jwt-auth/v1/token'
    payload = {'username': username, 'password': password}
    async with httpx.AsyncClient() as client:
        response = await client.post(auth_endpoint, json=payload, timeout=10)
    if response.status_code == 200:
        return response.json()['data']
    elif response.status_code == 403:
        print(f'Error 403: {response.json()["message"]}')
        return None
    else:
        print(f'Error: {response.json()["message"]}')
        return None


def verify_pw_hash(pw: str, pw_hash: str) -> bool:
    """Verifies a password against a phpass hash.

    Args:
        pw: The plaintext password.
        pw_hash: The hashed password.

    Returns:
        bool: True if the password is valid, False otherwise.
    """
    return phpass.verify(pw, pw_hash)


app = FastAPI()


@app.on_event('startup')
async def startup():
    """Starts the background task to deactivate expired sessions on application startup."""
    asyncio.create_task(deactivate_expired_sessions())


@app.get('/')
async def root():
    """Root endpoint for the API.

    Returns:
        dict: A welcome message.
    """
    return {'message': 'Welcome sensei!'}


@app.post('/login', response_model=TokenData)
async def login(user_login: str, user_pass: str) -> dict | JSONResponse:
    """
    Handles user login and returns a JWT token.

    Args:
        user_login: The user's login name or email.
        user_pass: The user's password.

    Returns:
        dict | JSONResponse: A dictionary containing the token data if successful,
                             or a JSONResponse with an error message.
    """
    data = get_wp_user_data(user_login)
    try:
        verified = verify_pw_hash(user_pass, data.user_pass)
    except AttributeError as e:
        print(f'CAUGHT ATTRIBUTE ERROR: {e}')
        verified = False
    if verified:
        token_data = await get_token_data(user_login, user_pass)
    else:
        return JSONResponse(
            status_code=401,
            content={'message': 'Login failed'}
        )
    return token_data


@app.post('/license/{action}')
async def license_api(action: str, username: str, client_id: int, token: str,
                      session_id: str) -> LicenseResponse | None:
    """
    Handles license activation, deactivation, and status checks.

    Args:
        action: The license action to perform ('activate', 'deactivate', 'status').
        username: The username associated with the license.
        client_id: The client's user ID.
        token: The JWT token for authentication.
        session_id: The unique session ID for this activation.

    Returns:
        LicenseResponse | None: A LicenseResponse object with the result of the operation,
                                or None if an error occurred.
    """
    # Possible values for action: 'status', 'activate', 'deactivate'
    if action == 'activate':
        if not await check_last_create_date(client_id):
            return LicenseResponse(
                success=False,
                message='Rate-limit exceeded. Slow down, sensei.',
                total_activations=0,
                activations_remaining=0
            )
    url = 'https://swadbot.com/'
    api_data = await get_wp_api_resource_data(client_id)
    # print(f'API_DATA: {api_data}')

    client_session = UserSession(
        token=token,
        username=username,
        user_id=client_id,
        product_id=api_data.product_id,
        master_api_key=api_data.master_api_key,
        this_session=session_id,
        ip='0.0.0.0',
        create_date=datetime.now(),
        last_access=datetime.now()
    )
    if action == 'activate':
        await client_session_write(client_session)
    elif action == 'status':
        await client_session_update(client_session)
    elif action == 'deactivate':
        await client_session_delete(client_session)

    params = {
        'wc-api': 'wc-am-api',
        'wc_am_action': action,
        'api_key': api_data.master_api_key,
        'instance': session_id,
        'product_id': api_data.product_id
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url=url,
            params=params,
            headers={'Authorization': f'Bearer {token}'},
            timeout=10
        )
        if response.status_code != 200:
            return None
        json_data = response.json()
        # print(f'JSON_DATA: {json_data}')

    ar = LicenseResponse(success=True, message='', total_activations=0, activations_remaining=0)
    if action == 'activate':
        ar.success = json_data['success']
        if 'message' in json_data:
            ar.message = json_data['message']
        elif 'error' in json_data:
            ar.message = json_data['error']
        if json_data['success']:
            ar.total_activations = json_data['data']['total_activations']
            ar.activations_remaining = json_data['data']['activations_remaining']
        else:
            ar.total_activations = 0
            ar.activations_remaining = 0
    elif action == 'status':
        ar.success = json_data['data']['activated']
        ar.message = json_data['status_check']
        ar.total_activations = json_data['data']['total_activations']
        ar.activations_remaining = json_data['data']['activations_remaining']
    return ar


async def deactivate_expired_sessions():
    """Periodically checks for and deactivates expired user sessions."""
    while True:
        async with AsyncSession(pg_engine) as session:
            statement = select(UserSession).where(
                UserSession.last_access < datetime.now() - timedelta(seconds=20))
            results = await session.execute(statement)
            for client_session in results.scalars():
                await license_api(
                    'deactivate',
                    client_session.username,
                    client_session.user_id,
                    client_session.token,
                    client_session.this_session
                )
                print(f'DEACTIVATED SESSION: {client_session}')
                await client_session_delete(client_session)
        await asyncio.sleep(10)


async def client_session_delete(client_session: UserSession):
    """Deletes a user session from the database.

    Args:
        client_session: The UserSession object to delete.
    """
    async with AsyncSession(pg_engine) as session:
        statement = delete(UserSession).where(
            UserSession.this_session == client_session.this_session)
        await session.execute(statement)
        await session.commit()
    # print(f'DELETED SESSION FROM DB: {client_session}')


async def client_session_update(client_session: UserSession):
    """Updates the last_access time of a user session in the database.

    Args:
        client_session: The UserSession object to update.
    """
    async with AsyncSession(pg_engine) as session:
        statement = update(UserSession).where(
            UserSession.this_session == client_session.this_session).values(
            last_access=datetime.now())
        await session.execute(statement)
        await session.commit()
    # print(f'UPDATED SESSION IN DB: {client_session}')


async def client_session_write(client_session: UserSession):
    """Writes a new user session to the database.

    Args:
        client_session: The UserSession object to write.
    """
    async with AsyncSession(pg_engine) as session:
        session.add(client_session)
        await session.commit()
        await session.refresh(client_session)
    # print(f'WROTE SESSION TO DB: {client_session}')


async def get_wp_api_resource_data(user_id: int) -> WPWCAMApiResource:
    """Retrieves API resource data for a user from the WordPress database.

    Args:
        user_id: The user's ID.

    Returns:
        WPWCAMApiResource: A WPWCAMApiResource object containing the resource data.
    """
    with Session(wp_engine) as session:
        statement = select(WPWCAMApiResource).where(WPWCAMApiResource.user_id == user_id)
        results = session.exec(statement).first()
    # print(f'F_RESULTS: {results}')
    return results


async def get_wp_api_activations_data(activation_ids: list[int]) -> list[WPWCAMApiActivation]:
    """Retrieves API activation data from the WordPress database.

    Args:
        activation_ids: A list of activation IDs to retrieve.

    Returns:
        list[WPWCAMApiActivation]: A list of WPWCAMApiActivation objects.
    """
    with Session(wp_engine) as session:
        total_results = []
        for client_id in activation_ids:
            statement = select(WPWCAMApiActivation).where(
                WPWCAMApiActivation.activation_id == client_id)
            results = session.exec(statement).first()
            total_results.append(results)
    # print(f'TOTAL_RESULTS: {total_results}')
    return total_results


async def check_last_create_date(client_id: int) -> bool:
    """
    Checks if a user has created a session recently to prevent rate-limiting abuse.

    Args:
        client_id: The user's ID.

    Returns:
        bool: False if a session was created within the last 5 seconds, True otherwise.
    """
    async with AsyncSession(pg_engine) as session:
        statement = select(
            UserSession).where(
            UserSession.user_id == client_id).where(
            UserSession.create_date > datetime.now() - timedelta(seconds=5)
        )
        results = await session.execute(statement)
        for _ in results.scalars():
            return False
    return True


def run():
    """Sets the asyncio event loop policy for Windows if applicable."""
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


if __name__ != '__main__':
    # NOT EQUALS!
    run()
