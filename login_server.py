import asyncio
import platform
from passlib.hash import phpass
from datetime import datetime, timedelta
from typing import Optional
from sqlmodel import Field, Session, SQLModel, engine, create_engine, select, update, delete
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import httpx


_username: str = 'socketserver'
_password: str = 'YwwF7bQcLiTMtwm'
_host: str = 'swadbot.com'
_port: int = 3306
_database: str = 'wordpress'

PG_PASSWORD = '^LOl}EIzU*/Y/-Ko'
PG_URI = f'postgresql+asyncpg://postgres:{PG_PASSWORD}@34.31.76.97/socket-sessions'


def get_wp_mysql_engine() -> engine:
    return create_engine(
        url=f'mysql+pymysql://{_username}:{_password}@{_host}:{_port}/{_database}',
        echo=False
    )


def get_pg_engine() -> AsyncEngine:
    return create_async_engine(url=PG_URI, echo=False)


wp_engine = get_wp_mysql_engine()   # Connects to WordPress MySQL
pg_engine = get_pg_engine()         # Connects to dedicated PostgresSQL


class WPUsers(SQLModel, table=True):
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
    token: str
    id: int
    email: str
    nicename: str
    firstName: str
    lastName: str
    displayName: str


class LicenseResponse(SQLModel):
    success: bool
    message: str
    total_activations: int
    activations_remaining: int




def get_wp_user_data(username: str) -> WPUsers:
    with Session(wp_engine) as session:
        # If user enters email as username then use email to find user
        if '@' in username and '.' in username:
            statement = select(WPUsers).where(WPUsers.user_email == username)
        else:
            statement = select(WPUsers).where(WPUsers.user_login == username)
        results = session.exec(statement).first()
        return results


async def get_token_data(username: str, password: str) -> dict | None:
    auth_endpoint = 'https://swadbot.com/wp-json/jwt-auth/v1/token'
    payload = {'username': username, 'password': password}
    async with httpx.AsyncClient() as client:
        response = await client.post(auth_endpoint, json=payload)
    if response.status_code == 200:
        return response.json()['data']
    elif response.status_code == 403:
        print(f'Error 403: {response.json()["message"]}')
        return None
    else:
        print(f'Error: {response.json()["message"]}')
        return None


def verify_pw_hash(pw: str, pw_hash: str) -> bool:
    return phpass.verify(pw, pw_hash)


app = FastAPI()


@app.on_event('startup')
async def startup():
    asyncio.create_task(deactivate_expired_sessions())


@app.post('/login', response_model=TokenData)
async def login(user_login: str, user_pass: str) -> dict | JSONResponse:
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

    # Possible values for action: 'status', 'activate', 'deactivate'

    url = 'https://swadbot.com/'
    api_data = await get_wp_api_resource_data(client_id)
    # print(f'API_DATA: {api_data}')
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
            headers={'Authorization': f'Bearer {token}'}
        )
        if response.status_code != 200:
            return None
        json_data = response.json()
        # print(f'JSON_DATA: {json_data}')
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
    async with AsyncSession(pg_engine) as session:
        statement = delete(UserSession).where(
            UserSession.this_session == client_session.this_session)
        await session.execute(statement)
        await session.commit()
    # print(f'DELETED SESSION FROM DB: {client_session}')


async def client_session_update(client_session: UserSession):
    async with AsyncSession(pg_engine) as session:
        statement = update(UserSession).where(
            UserSession.this_session == client_session.this_session).values(
            last_access=datetime.now())
        await session.execute(statement)
        await session.commit()
    # print(f'UPDATED SESSION IN DB: {client_session}')


async def client_session_write(client_session: UserSession):
    async with AsyncSession(pg_engine) as session:
        session.add(client_session)
        await session.commit()
        await session.refresh(client_session)
    # print(f'WROTE SESSION TO DB: {client_session}')


async def get_wp_api_resource_data(user_id: int) -> WPWCAMApiResource:
    with Session(wp_engine) as session:
        statement = select(WPWCAMApiResource).where(WPWCAMApiResource.user_id == user_id)
        results = session.exec(statement).first()
    # print(f'F_RESULTS: {results}')
    return results


async def get_wp_api_activations_data(activation_ids: list[int]) -> list[WPWCAMApiActivation]:
    with Session(wp_engine) as session:
        total_results = []
        for client_id in activation_ids:
            statement = select(WPWCAMApiActivation).where(
                WPWCAMApiActivation.activation_id == client_id)
            results = session.exec(statement).first()
            total_results.append(results)
    # print(f'TOTAL_RESULTS: {total_results}')
    return total_results


async def test_system():
    token_data = await get_token_data('test1', 'swadbotpass123')
    print(f'TOKEN DATA: {token_data}')
    if token_data is None:
        return None

    wp_data = get_wp_user_data(token_data['nicename'])
    print(f'WP DATA: {wp_data}')
    if wp_data is None:
        return None

    api_data = await get_wp_api_resource_data(wp_data.ID)
    print(f'API DATA: {api_data}')
    if api_data is None:
        return None

    license_api_data = await license_api(
        token_data['nicename'],
        'status',
        token_data['token'],
        api_data.master_api_key,
        'THIS-IS-A-SESSION-KEY',
        api_data.product_id
    )
    print(f'LICENSE API DATA: {license_api_data}')


def run():
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


if __name__ == '__main__':
    run()
    asyncio.run(test_system())
else:
    run()
