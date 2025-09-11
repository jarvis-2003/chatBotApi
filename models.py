from pydantic import BaseModel
from typing import Optional

class Answers(BaseModel):
    session_id: str
    name: str
    answer: str | list[str]

class fuzzycheck(BaseModel):
    locations: str
    loclist : list[str]

class validateEmailPhone(BaseModel):
    session_id: str
    email: Optional[str] = None
    phone: Optional[int] = None 