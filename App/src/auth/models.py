from sqlmodel import Field, SQLModel
from datetime import datetime, timezone


def get_datetime():
    return datetime.now(timezone.utc)


class User(SQLModel, table = True):
    id : int | None = Field(default=None, primary_key=True)
    nume: str | None = Field(max_length=150)
    email: str = Field(unique=True, index=True, max_length=150)
    hashed_password: str = Field(min_length=8, max_length=120) #saving in db a hashed password ... NEVER SAVE NORMAL PASSWORD IN DB!
    created_at : datetime = Field(default_factory=get_datetime)


class ScanHistory(SQLModel, table = True):
    id : int | None = Field(default=None, primary_key=True)
    user_id : int = Field(foreign_key="user.id", index = True)
    image_url : str
    ocr_text: str
    ingredients_json: str             # JSON string of scored ingredients
    summary_json: str                 # JSON string of risk counts
    created_at : datetime = Field(default_factory=get_datetime)
     