# Src/Core/models.py
from pydantic import BaseModel

class GraphState(BaseModel):
    user_input: str = ""
    response: str = ""