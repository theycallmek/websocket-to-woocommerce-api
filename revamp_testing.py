from typing import List, Optional
from fastapi import FastAPI, HTTPException
from sqlmodel import Field, SQLModel, create_engine, Session, select
import os

class WpPost(SQLModel, table=True):
    __tablename__ = "wp_posts"

    ID: Optional[int] = Field(default=None, primary_key=True)
    post_author: int
    post_date: str  # You might want to use datetime.datetime
    post_date_gmt: str
    post_content: str
    post_title: str
    post_excerpt: str
    post_status: str
    comment_status: str
    ping_status: str
    post_password: str
    post_name: str
    to_ping: str
    pinged: str
    post_modified: str
    post_modified_gmt: str
    post_content_filtered: str
    post_parent: int
    guid: str
    menu_order: int
    post_type: str
    post_mime_type: str
    comment_count: int

    class Config:
        orm_mode = True


app = FastAPI()

# Database credentials (consider using environment variables for production)
DB_HOST = os.getenv("WP_MYSQL_HOST", "swadbot.com")
DB_USER = os.getenv("WP_MYSQL_PASS", "login-server-agent")
DB_PASSWORD = os.getenv("WP_MYSQL_PASS", "7@jL&rA9!sW3*fHk")
DB_NAME = os.getenv("WP_MYSQL_DB_NAME", "wordpress")

DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    """
    This function is typically used to create tables based on SQLModel definitions.
    For an existing WordPress database, you usually don't need to create tables.
    However, it's good practice to have it for schema synchronization if you were
    managing the schema directly with SQLModel.
    """
    # SQLModel.metadata.create_all(engine) # Uncomment if you need to create tables
    pass

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/")
async def read_root():
    return {"message": "Welcome to the WordPress API with FastAPI and SQLModel!"}

@app.get("/posts/", response_model=List[WpPost])
async def read_posts(offset: int = 0, limit: int = 10):
    try:
        with Session(engine) as session:
            statement = select(WpPost).offset(offset).limit(limit)
            posts = session.exec(statement).all()
            return posts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching posts: {e}")

@app.get("/posts/{post_id}", response_model=WpPost)
async def read_post(post_id: int):
    try:
        with Session(engine) as session:
            post = session.get(WpPost, post_id)
            if not post:
                raise HTTPException(status_code=404, detail="Post not found")
            return post
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching post: {e}")

# To run this FastAPI application:
# 1. Make sure you have uvicorn installed: pip install uvicorn
# 2. Save this file as, for example, `main.py`.
# 3. Run from your terminal: `uvicorn main:app --reload`
# 4. Access the API at http://127.0.0.1:8000/
#    - http://127.0.0.1:8000/posts/ to get a list of posts
#    - http://127.0.0.1:8000/posts/1 to get a specific post (replace 1 with an actual post ID)
#    - http://127.0.0.1:8000/docs for interactive API documentation (Swagger UI)
#    - http://127.0.0.1:8000/redoc for ReDoc documentation
