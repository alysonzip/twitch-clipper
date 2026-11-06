from sqlmodel import SQLModel, create_engine, Session
from pathlib import Path

# Database file in user's AppData folder
DB_PATH = Path.home() / "AppData" / "Local" / "TwitchClipper" / "data.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session