from sqlmodel import SQLModel, Session, create_engine
from config import DB_PATH


DATABASE_URL = f"sqlite:///{DB_PATH}"



connect_args = {"check_same_thread": False}
engine = create_engine(DATABASE_URL, connect_args=connect_args)


def create_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session    


def get_session_direct():
    return Session(engine)        