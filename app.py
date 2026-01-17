# Fix OpenMP duplicate library error on macOS
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from fastapi import FastAPI, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import services.agent_service as agent_service
from utils.helper_functions import register_merchant, register_user,get_user,get_user_by_upi_id
from utils.schemas import (
    RegisterRequestSchema,
    RegisterResponseSchema,
    AgentChatRequestSchema,
    AgentChatResponseSchema,
    RegisterUserRequestSchema,
    RegisterUserResponseSchema,
    GetUserResponseSchema
)
import time
import uvicorn
import httpx
from dotenv import load_dotenv
load_dotenv()

COIN_GECKO_API_KEY = os.getenv("COIN_GECKO_API_KEY")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

COMMON_HEADERS = {
    "X-Service-Name": "agent-api",
    "X-Service-Status": "ok",
}

@app.get("/")
def health_check(response: Response):
    response.headers.update(COMMON_HEADERS)
    response.headers["X-Timestamp"] = str(time.time())
    return {"status": "healthy", "time": time.time()}

@app.post("/register-merchant")
async def register_merchant_handler(request: RegisterRequestSchema) -> RegisterResponseSchema:
    result = register_merchant(
        request.wallet_address,
        request.username,
        request.business_type,
        request.description,
        request.business_upi_id,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Registration failed"))
    return RegisterResponseSchema(status="success", username=request.username)

@app.post("/register-user")
async def register_user_handler(request: RegisterUserRequestSchema) -> RegisterUserResponseSchema:
    register_user(request.username, request.upi_id, request.wallet_address)
    return RegisterUserResponseSchema(status="success", username=request.username)

@app.get("/get-user-from-wallet-address")
async def get_user_from_wallet_address_handler(wallet_address: str) -> GetUserResponseSchema:
    user = get_user(wallet_address)
    if user is not None:
        return GetUserResponseSchema(username=user["name"], upi_id=user["upi_id"], wallet_address=user["wallet_address"])
    else:
        return GetUserResponseSchema(username="", upi_id="", wallet_address="", error="User not found")

@app.get("/get-user-from-upi-id")
async def get_user_from_upi_id_handler(upi_id: str) -> GetUserResponseSchema:
    user = get_user_by_upi_id(upi_id)
    if user is not None:
        return GetUserResponseSchema(username=user["name"], upi_id=user["upi_id"], wallet_address=user["wallet_address"])
    else:
        return GetUserResponseSchema(username="", upi_id="", wallet_address="", error="User not found")
    
@app.post("/agent/chat")
async def agent_chat(request: AgentChatRequestSchema) -> AgentChatResponseSchema:
    response_data = agent_service.run_agent(request.message)
    return AgentChatResponseSchema(text=response_data["text"], auto_fill=response_data["auto_fill"])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001, reload=True)
