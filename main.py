from fastapi import APIRouter, HTTPException, Query
from storage import get_data_by_brand
from scraping.manager import trigger_scraping
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

router = APIRouter(prefix="/api/v1/gold", tags=["gold"])
app = FastAPI(title="Gold Price API")
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://127.0.0.1",
    "http://127.0.0.1:3000",
    "https://daily-test-frontend.vercel.app"
    # Add your frontend domain(s) here
]

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@router.get("/price", response_model=None)
def get_gold_price(brand: str = Query(..., description="e.g. doji, pnj, mihong, sjc, btmh, btmc")):
    trigger_scraping(brand)
    data = get_data_by_brand(brand)
    if not data:
        raise HTTPException(status_code=404, detail=f"Brand '{brand}' not found")
    return data

app.include_router(router)
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

