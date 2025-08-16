from typing import List
from pydantic import BaseModel


class Record(BaseModel):
    question: str
    answer: str

class Response(BaseModel):
    generated: List[Record]