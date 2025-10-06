import time
import traceback
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Request, HTTPException, Depends, Header
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.providers.sense_provider import SenseProvider

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.DESCRIPTION
)

sense_provider = SenseProvider()

async def verify_api_key(authorization: Optional[str] = Header(None)):
    if not settings.API_MASTER_KEY:
        return

    if authorization is None:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Missing Authorization header.",
        )
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid scheme")
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication scheme. Use 'Bearer <your_api_key>'.",
        )
    
    if token != settings.API_MASTER_KEY:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Invalid API Key.",
        )

@app.on_event("shutdown")
async def shutdown_event():
    await sense_provider.close()

@app.post("/v1/chat/completions", dependencies=[Depends(verify_api_key)])
async def chat_completions(request: Request):
    try:
        request_data = await request.json()
        return await sense_provider.chat_completion(request_data)
    except Exception as e:
        traceback.print_exc()
        error_message = f"Internal Server Error in main route: {str(e)}"
        return JSONResponse(
            status_code=500, 
            content={"error": {"message": error_message, "type": "internal_error"}}
        )

@app.get("/v1/models", dependencies=[Depends(verify_api_key)])
async def list_models():
    model_names: List[str] = settings.supported_models
    
    model_data: List[Dict[str, Any]] = []
    for name in model_names:
        model_data.append({
            "id": name,
            "object": "model",
            "created": int(time.time()),
            "owned_by": "sensetime"
        })
        
    return {
        "object": "list",
        "data": model_data
    }

@app.get("/")
def root():
    return {"message": f"Welcome to {settings.APP_NAME}", "version": settings.APP_VERSION}
