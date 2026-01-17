from pydantic import BaseModel
from typing import Optional

class RegisterRequestSchema(BaseModel):
    username: str
    wallet_address: str
    description: str
    business_type: str
    business_upi_id: str
    
class RegisterResponseSchema(BaseModel):
    status: str
    username: str
    
class AgentChatResponseSchema(BaseModel):
    text: str
    auto_fill: Optional[dict] = None
    
class AgentChatRequestSchema(BaseModel):
    message: str
    
class RegisterUserRequestSchema(BaseModel):
    username: str
    upi_id: str
    wallet_address: str
    
class RegisterUserResponseSchema(BaseModel):
    status: str
    username: str
    
class GetUserResponseSchema(BaseModel):
    username: str
    upi_id: str
    wallet_address: str
    error: Optional[str] = None