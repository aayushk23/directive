from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


ASK_REQUEST_EXAMPLE = {
    "question": "What should employees do if they suspect account compromise?"
}


class AskRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [ASK_REQUEST_EXAMPLE]}
    )

    question: Annotated[str, Field(min_length=1)]

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("question must not be blank")
        return value


class Citation(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "document_id": "it-password-policy",
                    "title": "IT Password Policy",
                    "snippet": (
                        "Employees must rotate passwords every 90 days. Employees "
                        "who suspect account compromise must immediately contact "
                        "IT Security."
                    ),
                }
            ]
        }
    )

    document_id: str
    title: str
    snippet: str


class AskResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "answer": (
                        "Employees must rotate passwords every 90 days and "
                        "immediately report suspected account compromise to IT "
                        "Security."
                    ),
                    "supported": True,
                    "citations": [
                        {
                            "document_id": "it-password-policy",
                            "title": "IT Password Policy",
                            "snippet": (
                                "Employees must rotate passwords every 90 days. "
                                "Employees who suspect account compromise must "
                                "immediately contact IT Security."
                            ),
                        }
                    ],
                    "refusal_reason": None,
                }
            ]
        }
    )

    answer: str
    supported: bool
    citations: list[Citation]
    refusal_reason: str | None
