from pydantic import BaseModel, Field


class AIRecordRequest(BaseModel):
    ai_request: str = Field(
        ...,
        min_length=1,
        description="The prompt or request sent to the AI system."
    )

    ai_response: str = Field(
        ...,
        min_length=1,
        description="The response returned by the AI system."
    )


class ReceiptResponse(BaseModel):
    record_id: int
    receipt: str
    previous_hash: str
    created_at: str


class VerificationResponse(BaseModel):
    record_id: int
    valid: bool
    status: str
    reason: str