from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],  # Allow GET requests
    allow_headers=["*"],
)

EXTERNAL_URL = "https://b9a5-2406-7400-10a-dbc4-4900-aaa7-d609-7fcb.ngrok-free.app/api/ver/"

@app.get("/api")  # ✅ Change to GET
async def proxy_endpoint(name: list[str] = Query(...)):
    try:
        params = [("name", n) for n in name]
        async with httpx.AsyncClient(timeout=10) as client:
            external_resp = await client.get(EXTERNAL_URL, params=params)  # ✅ Change to GET
        external_resp.raise_for_status()
        data = external_resp.json()
        return data
    except Exception as e:
        return {"error": str(e)}
