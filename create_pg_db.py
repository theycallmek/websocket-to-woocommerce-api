from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel, create_engine, engine

_username: str = 'socketserver'
_password: str = 'YwwF7bQcLiTMtwm'
_host: str = 'swadbot.com'
_port: int = 3306
_database: str = 'wordpress'

PG_PASSWORD = "^LOl}EIzU*/Y/-Ko"
PG_URI = f'postgresql+pg8000://postgres:{PG_PASSWORD}@34.31.76.97/socket-sessions'


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


def create_db_and_tables():

    def create_db_maker_engine():
        return create_engine(url=PG_URI, echo=True)

    engine_ = create_db_maker_engine()
    SQLModel.metadata.create_all(engine_)


if __name__ == '__main__':
    create_db_and_tables()
