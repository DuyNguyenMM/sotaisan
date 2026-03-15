from fastapi import APIRouter, HTTPException, Query
from storage import get_data_by_brand
from scraping.manager import trigger_scraping
from schemas import GoldResponse
from fastapi import FastAPI
router = APIRouter(prefix="/api/v1/gold", tags=["gold"])

@router.get("/price", response_model=None)
def get_gold_price(brand: str = Query(..., description="e.g. doji, pnj, mihong, sjc, btmh, btmc")) -> GoldResponse:
    trigger_scraping(brand)
    data = get_data_by_brand(brand)
    if not data:  # ✅ data is None or empty list → brand not found
        raise HTTPException(status_code=404, detail=f"Brand '{brand}' not found")
    return data

app = FastAPI(title="Gold Price API")
app.include_router(router)