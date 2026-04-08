from pydantic import BaseModel


class UserContext(BaseModel):
    uid: str
    email: str | None = None
