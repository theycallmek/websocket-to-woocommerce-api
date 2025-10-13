import os
from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel, create_engine, engine
import dotenv

dotenv.load_dotenv()
PG_URI = (
    f'postgresql+pg8000://{os.environ["PG_USER"]}'
    f':{os.environ["PG_PASSWORD"]}'
    f'@{os.environ["PG_HOST"]}'
    f'/{os.environ["PG_DB_NAME"]}'
)


class UserSession(SQLModel, table=True):
    __tablename__: str = 'user_sessions'
    id: Optional[int] = Field(default=None, primary_key=True)
    token: str
    username: str
    user_id: int
    product_id: int
    master_api_key: str
    this_session: str = Field(index=True)
    ip: Optional[str] = Field(default='0.0.0.0')
    create_date: Optional[datetime] = Field(default=datetime.now())
    last_access: Optional[datetime] = Field(default=datetime.now(), index=True)


class Logs(SQLModel, table=True):
    __tablename__: str = 'logs'
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    ip: str
    message: str
    create_date: Optional[datetime] = Field(default=datetime.now(), index=True)


def create_db_and_tables():

    def create_db_maker_engine() -> engine:
        return create_engine(url=PG_URI, echo=True)

    engine_ = create_db_maker_engine()
    SQLModel.metadata.create_all(engine_)


if __name__ == '__main__':
    create_db_and_tables()
