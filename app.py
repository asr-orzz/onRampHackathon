from fastapi import FastAPI, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import services.agent_service as agent_service
from utils.helper_functions import register_merchant
from utils.schemas import (
    RegisterRequestSchema,
    RegisterResponseSchema,
    AgentChatRequestSchema,
    AgentChatResponseSchema,
)
import time
import uvicorn

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

@app.api_route("/ping", methods=["GET", "HEAD"])
def ping(response: Response):
    response.headers.update(COMMON_HEADERS)
    response.headers["X-Timestamp"] = str(time.time())
    # Use Response explicitly so HEAD returns headers correctly without body
    return Response(content="pong", media_type="text/plain")

# Optional: silence favicon noise
@app.api_route("/favicon.ico", methods=["GET", "HEAD"])
def favicon():
    return Response(status_code=204)

@app.post("/register")
async def register(request: RegisterRequestSchema) -> RegisterResponseSchema:
    result = register_merchant(
        request.wallet_address,
        request.username,
        request.business_type,
        request.description,
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Registration failed"))
    return RegisterResponseSchema(status="success", username=request.username)

@app.post("/agent/chat")
async def agent_chat(request: AgentChatRequestSchema) -> AgentChatResponseSchema:
    response_data = agent_service.run_agent(request.message)
    return AgentChatResponseSchema(text=response_data["text"], auto_fill=response_data["auto_fill"])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001, reload=True)
