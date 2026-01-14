from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import services.agent_service as agent_service
from utils.helper_functions import register_merchant
from utils.schemas import (
    RegisterRequestSchema,
    RegisterResponseSchema,
    AgentChatRequestSchema,
    AgentChatResponseSchema
)
import time
import uvicorn

app = FastAPI()

# Enable CORS for all origins (adjust as needed)
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
    return {
        "status": "healthy",
        "time": time.time()
    }

@app.get("/ping")
def ping(response: Response):
    """
    Lightweight endpoint for UptimeRobot / load balancers
    """
    response.headers.update(COMMON_HEADERS)
    response.headers["X-Timestamp"] = str(time.time())
    return "pong"

@app.post("/register")
async def register(request: RegisterRequestSchema) -> RegisterResponseSchema:
    register_merchant(
        request.wallet_address,
        request.username,
        request.business_type,
        request.description
    )
    return RegisterResponseSchema(
        status="success",
        username=request.username
    )

@app.post("/agent/chat")
async def agent_chat(
    request: AgentChatRequestSchema
) -> AgentChatResponseSchema:
    response_data = agent_service.run_agent(request.message)
    return AgentChatResponseSchema(
        text=response_data["text"],
        auto_fill=response_data["auto_fill"]
    )

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5001,
        reload=True
    )
