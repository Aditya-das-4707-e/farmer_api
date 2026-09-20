from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(
    title="Indian Market Price API",
    description="Search product name, get general market price. Example: /products/search?name=rice",
    version="2.0.0",
)

# ---------------- Model: market price only (no farmer) ----------------

class ProductPrice(BaseModel):
    id: int
    product_name: str
    hindi_name: Optional[str] = None
    bengali_name: Optional[str] = None
    market_price_per_kg: float  # INR per kg - general market rate
    unit: str = "kg"
    currency: str = "INR"
    market_price: Optional[str] = None  # e.g. "Rs 28 per kg"


# ---------------- Data: one market price per product ----------------

products_db: List[ProductPrice] = [
    ProductPrice(id=1, product_name="rice", hindi_name="चावल", bengali_name="চাল", market_price_per_kg=65.0),
    ProductPrice(id=2, product_name="wheat", hindi_name="गेहूं", bengali_name="গম", market_price_per_kg=38.0),
    ProductPrice(id=3, product_name="sugarcane", hindi_name="गन्ना", bengali_name="আখ", market_price_per_kg=4.0),
    ProductPrice(id=4, product_name="cotton", hindi_name="कपास", bengali_name="তুলা", market_price_per_kg=75.0),
    ProductPrice(id=5, product_name="maize", hindi_name="मक्का", bengali_name="ভুট্টা", market_price_per_kg=30.0),
    ProductPrice(id=6, product_name="soybean", hindi_name="सोयाबीन", bengali_name="সয়াবিন", market_price_per_kg=55.0),
    ProductPrice(id=7, product_name="mustard", hindi_name="सरसों", bengali_name="সরিষা", market_price_per_kg=65.0),
    ProductPrice(id=8, product_name="groundnut", hindi_name="मूंगफली", bengali_name="চিনাবাদাম", market_price_per_kg=110.0),
    ProductPrice(id=9, product_name="onion", hindi_name="प्याज", bengali_name="পেঁয়াজ", market_price_per_kg=40.0),
    ProductPrice(id=10, product_name="potato", hindi_name="आलू", bengali_name="আলু", market_price_per_kg=28.0),
    ProductPrice(id=11, product_name="tomato", hindi_name="टमाटर", bengali_name="টমেটো", market_price_per_kg=35.0),
    ProductPrice(id=12, product_name="mango", hindi_name="आम", bengali_name="আম", market_price_per_kg=140.0),
    ProductPrice(id=13, product_name="banana", hindi_name="केला", bengali_name="কলা", market_price_per_kg=50.0),
    ProductPrice(id=14, product_name="turmeric", hindi_name="हल्दी", bengali_name="হলুদ", market_price_per_kg=170.0),
    ProductPrice(id=15, product_name="chilli", hindi_name="मिर्च", bengali_name="লঙ্কা", market_price_per_kg=200.0),
    ProductPrice(id=16, product_name="tea", hindi_name="चाय", bengali_name="চা", market_price_per_kg=280.0),
]


def find_by_product(name: str) -> Optional[ProductPrice]:
    name = name.strip().lower()
    for p in products_db:
        if p.product_name.lower() == name:
            return p
    return None


# ---------------- Routes (search only) ----------------

# @app.get("/")
# def home():
#     return {
#         "message": "Welcome to Indian Market Price API",
#         "usage": "GET /products/?name=rice",
#     }


@app.get("/products/", response_model=ProductPrice)
def search_product(name: str = Query(..., description="Product name e.g. rice, wheat, onion")):
    """
    User puts product name, market price comes.
    Example: GET /products/?name=rice
    """
    result = find_by_product(name)
    if not result:
        raise HTTPException(status_code=404, detail=f"No product found with name '{name}'")
    # Add Rs formatted price, e.g. "Rs 28 per kg"
    result.market_price = f"Rs {result.market_price_per_kg:g} per {result.unit}"
    return result
