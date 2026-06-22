from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1)
