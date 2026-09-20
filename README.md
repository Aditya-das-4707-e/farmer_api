# Indian Market Price API

> **Live:** https://farmer-api-ooi2.onrender.com/ · Swagger UI: https://farmer-api-ooi2.onrender.com/docs

A lightweight FastAPI service that returns general Indian market prices (INR) for agricultural products. Search by product name — plural-tolerant — and get the market rate with Hindi and Bengali names.

Example: `GET https://farmer-api-ooi2.onrender.com/products/?name=rice` → market price(s) for rice varieties.

> Version 4.0.0 · `main.py` + `gov_client.py` + `mapper.py` + `price_cache.py` · 411 curated products · No database required.
>
> **Data status: live govt + static fallback.** `GET /products/?name=` returns the all-India Agmarknet modal average (via `data.gov.in` resource `9ef84268-d588-465a-a308-a864a43d0070`) converted to Rs/kg where a mandi series exists (`source: live/cache`), otherwise the curated static price (`source: static_fallback`, e.g. ghee, paneer, honey, milk, oils, pickles). Set `DATA_GOV_IN_API_KEY` to enable live; without a key the API still works on static data.

## Features

- **Name search** — `GET /products/` with `?name=` query param.
- **Live govt prices** — all-India Agmarknet modal average via `data.gov.in`, converted Rs/quintal ÷ 100 → Rs/kg (`source: live/cache`, with `arrival_date`, `markets_count`, `min/max_price_per_kg`, `matched_commodity`). Non-mandi items (ghee, paneer, honey, milk, oils, pickles…) stay curated static (`source: static_fallback`).
- **State filter** — `?state=West Bengal` averages only that state's mandis (default empty = all-India). Case-insensitive, e.g. `west bengal` works. `?live=false` forces static prices.
- **Plural-tolerant matching** — `potato` / `potatos` / `potatoes` all match; same for `onion/onions`, `tomato/tomatoes`, `chilli/chillies`, etc.
- **Generic-term expansion** — `egg` → Poultry Egg + Duck Egg, `honey` → all honeys, `milk` → all milks, `mango` → all mangoes.
- **3-tier match strategy** — exact normalized match → whole-word match → substring fallback.
- **Trilingual names** — English `product_name` + `hindi_name` + `bengali_name`.
- **Formatted price** — `market_price` string like `"Rs 28 per kg"` auto-added per response.
- **Zero-config data** — in-memory list (`RAW_PRODUCTS`), auto IDs, Title-Cased names.
- **Auto docs** — Swagger UI at `/docs`, ReDoc at `/redoc`.

## Tech Stack

| Layer | Choice |
|---|---|
| Framework | FastAPI 0.101.0 |
| Server | Uvicorn 0.23.2 |
| Validation | Pydantic 2.4.2 |
| Language | Python 3.12 (see `.python-version`; 3.8+ should work) |
| Storage | In-memory product catalog (`RAW_PRODUCTS`) + 6h in-memory live-price cache (`price_cache.py`); no DB |
| Live data | Agmarknet via `data.gov.in` resource `9ef84268-d588-465a-a308-a864a43d0070` (`gov_client.py`), needs `DATA_GOV_IN_API_KEY` |
| Hosting | Render — live at https://farmer-api-ooi2.onrender.com/ |

See `requirements.txt`.

## Live Deployment

- **Base URL:** https://farmer-api-ooi2.onrender.com/
- **Swagger UI:** https://farmer-api-ooi2.onrender.com/docs
- **ReDoc:** https://farmer-api-ooi2.onrender.com/redoc
- **Health check:** just open the base URL (FastAPI root) or hit the example below.

Try it now (no setup needed):

```bash
curl "https://farmer-api-ooi2.onrender.com/products/?name=potato"
curl "https://farmer-api-ooi2.onrender.com/products/?name=honey"
curl "https://farmer-api-ooi2.onrender.com/products/?name=egg"
```

> Note: Render free-tier instances may cold-start (first request can take ~30–60s), then respond normally.

## Project Structure

```
farmer_api/
├── main.py            # App, data (RAW_PRODUCTS), search logic, routes (incl. ?state=, ?live=)
├── gov_client.py      # data.gov.in fetch + national/state average (Rs/quintal)
├── mapper.py          # product name -> govt commodity candidates
├── price_cache.py     # 6h in-memory cache
├── requirements.txt   # fastapi, uvicorn, pydantic, requests (pinned)
├── README.md          # This file
├── .env.example       # template for DATA_GOV_IN_API_KEY (copy to .env, never commit .env)
├── .python-version    # Python 3.12
├── .gitignore         # ignores /env, /__pycache__, .env
├── env/               # Local virtualenv (ignored, not committed)
└── __pycache__/       # Bytecode cache (ignored)
```

## Getting Started (Local Development)

Live API above is ready to use — the steps below are only for running/modifying it locally.

### 1. Prerequisites

- Python 3.8+ (`python3 --version`)

### 2. Clone & install

```bash
git clone <your-repo-url>
cd farmer_api

python3 -m venv env
source env/bin/activate        # Windows: env\Scripts\activate

pip install -r requirements.txt
cp .env.example .env           # then put your free data.gov.in key in .env as DATA_GOV_IN_API_KEY
```

### 3. Run

```bash
uvicorn main:app --reload
```

- API: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

Custom host/port:

```bash
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

## API Reference

### `GET /products/`

Search products by name, with live govt pricing.

| Param | Type | Required | Description |
|---|---|---|---|
| `name` | string | Yes | Product name. Plural-tolerant, case-insensitive. Generic terms return multiple items. E.g. `potato`, `RICE`, `egg`, `honey`. |
| `state` | string | No | State filter for the live average, e.g. `West Bengal`, `Punjab`. Case-insensitive. Default empty = all-India average. Non-mandi items ignore it (static fallback). |
| `live` | boolean | No | Default `true`. Set `live=false` to force curated static prices. |

**Success:** `200 OK` — JSON array of `ProductPrice`.
**Not found:** `404` — `{"detail": "No product found with name '<name>'"}`.
**Missing param:** `422` — FastAPI validation error.

#### Response schema (`ProductPrice`)

```json
{
  "id": 10,
  "product_name": "Potato",
  "hindi_name": "आलू",
  "bengali_name": "আলু",
  "market_price_per_kg": 12.07,
  "unit": "kg",
  "currency": "INR",
  "market_price": "Rs 12.07 per kg",
  "source": "live",
  "arrival_date": "20/09/2026",
  "markets_count": 3,
  "min_price_per_kg": 6.0,
  "max_price_per_kg": 16.0,
  "matched_commodity": "Potato"
}
```

| Field | Type | Notes |
|---|---|---|
| `id` | int | Auto index (1-based, curated order) |
| `product_name` | string | Title-Cased English name |
| `hindi_name` | string \| null | Hindi name (Devanagari) |
| `bengali_name` | string \| null | Bengali name |
| `market_price_per_kg` | float | Numeric price (despite name, value is per `unit`) |
| `unit` | string | `kg` (default), `litre`, or `piece` |
| `currency` | string | Always `INR` |
| `market_price` | string \| null | Formatted `"Rs <price> per <unit>"`, set at request time |
| `source` | string \| null | `"live"` (fresh fetch), `"cache"` (6h cached live avg), or `"static_fallback"` (curated price, no mandi series) |
| `arrival_date` | string \| null | Latest govt `arrival_date` (`DD/MM/YYYY`), live items only |
| `markets_count` | int \| null | Number of mandi records averaged, live items only |
| `min_price_per_kg` | float \| null | Min of the averaged mandis, Rs/kg, live items only |
| `max_price_per_kg` | float \| null | Max of the averaged mandis, Rs/kg, live items only |
| `matched_commodity` | string \| null | Exact govt commodity used, e.g. `Potato`, `Paddy(Basmati)` |

### Examples

How to call with product name + state (local and deployed are identical except the base URL):

```bash
# 1. All-India live average (default when ?state= is omitted)
curl "http://127.0.0.1:8000/products/?name=potato"
# -> Potato ~30-33 Rs/kg, source live/cache, markets_count ~150+

# 2. State average — West Bengal only (your Rs 15 morning-market case)
curl "http://127.0.0.1:8000/products/?name=potato&state=West%20Bengal"
# -> Potato ~12.07 Rs/kg, source live, markets_count 3, arrival_date 20/09/2026

# 3. Any state works the same way (case-insensitive)
curl "http://127.0.0.1:8000/products/?name=onion&state=Punjab"
curl "http://127.0.0.1:8000/products/?name=rice&state=Uttar%20Pradesh"

# 4. Force static curated price (no live lookup)
curl "http://127.0.0.1:8000/products/?name=potato&live=false"
# -> Potato 28.0 Rs/kg, source static_fallback
```

Live examples (swap the base URL with `http://127.0.0.1:8000` for local):

```bash
curl "https://farmer-api-ooi2.onrender.com/products/?name=potato"
curl "https://farmer-api-ooi2.onrender.com/products/?name=potatoes"  # same result
curl "https://farmer-api-ooi2.onrender.com/products/?name=RICE"
```

Exact match (local):

```bash
curl "http://127.0.0.1:8000/products/?name=potato"
curl "http://127.0.0.1:8000/products/?name=potatoes"  # same result
curl "http://127.0.0.1:8000/products/?name=RICE"
```

```json
[
  {
    "id": 10,
    "product_name": "Potato",
    "hindi_name": "आलू",
    "bengali_name": "আলু",
    "market_price_per_kg": 12.07,
    "unit": "kg",
    "currency": "INR",
    "market_price": "Rs 12.07 per kg",
    "source": "live",
    "arrival_date": "20/09/2026",
    "markets_count": 3,
    "min_price_per_kg": 6.0,
    "max_price_per_kg": 16.0,
    "matched_commodity": "Potato"
  }
]
```

State-filtered (West Bengal — matches the Swagger screenshot above):

```bash
curl "http://127.0.0.1:8000/products/?name=potato&state=West%20Bengal"
curl "https://farmer-api-ooi2.onrender.com/products/?name=potato&state=West%20Bengal"
```

Generic term (multiple results, live):

```bash
curl "https://farmer-api-ooi2.onrender.com/products/?name=egg"
curl "https://farmer-api-ooi2.onrender.com/products/?name=honey"
curl "https://farmer-api-ooi2.onrender.com/products/?name=milk"
```

Local equivalents:

```bash
curl "http://127.0.0.1:8000/products/?name=egg"
curl "http://127.0.0.1:8000/products/?name=honey"
curl "http://127.0.0.1:8000/products/?name=milk"
```

```bash
# 404 example
curl "http://127.0.0.1:8000/products/?name=xyz123"
# {"detail":"No product found with name 'xyz123'"}
```

Python example:

```python
import requests
r = requests.get("http://127.0.0.1:8000/products/", params={"name": "onions"})
print(r.json())

# With state filter (West Bengal average instead of all-India):
r = requests.get(
    "http://127.0.0.1:8000/products/",
    params={"name": "potato", "state": "West Bengal"},
)
print(r.json())
# [{"product_name": "Potato", "market_price_per_kg": 12.07, "source": "live", ...}]
```

## How Search Works

`main.py:458-523` — all logic in `normalize_word()` / `normalize_name()` / `find_all_by_product()`.

1. **Normalization** — lowercase, strip punctuation, collapse whitespace, then per-word plural stripping:
   - `ies → i` (`chillies → chilli`), `oes → drop -es` (`potatoes → potato`, `mangoes → mango`), `ches/shes/sses/xes/zes → drop -es` (`peaches → peach`), trailing `s → drop` (`onions → onion`, typo `potatos → potato`), `leaves → leaf`, trailing `y → i` (`chilly → chilli`).
2. **Tier 1 – exact normalized match** → single item (e.g. `raw honey` → Raw Honey).
3. **Tier 2 – whole-word match** → every query word appears as a whole word in the product (e.g. `honey` → all honeys, `milk` → all milks, not Milky Mushroom). Sorted by fewest extra words, then curated `id`.
4. **Tier 3 – substring fallback** → `key in norm or norm in key`.

Precomputed index: `_normalized_index` (dict) + `_normalized_list` (list) at import time.

## Data Coverage (Live Govt + Static Fallback)

411 entries in `RAW_PRODUCTS` (`main.py:28-440`), each `(name, hindi, bengali, price, unit)` — the catalog, trilingual names, and fallback prices.

Categories: cereals & millets (rice varieties, wheat, maize, jowar, bajra, ragi…), pulses & dals, vegetables & greens, mushrooms, fruits (mango/banana/orange/grape variants…), oilseeds, fibres (cotton, jute), plantation (tea, coffee, cocoa, rubber, areca, cashew, tobacco), spices (turmeric → saffron), medicinal/aromatic plants, flowers, dairy/poultry/meat/fish/seafood, honey & bee products, silk cocoons, and value-added goods (jaggery, flour, oils, ghee, paneer, pickles, juices, papad…).

Units: mostly `kg`; milk/oils/buttermilk in `litre`; eggs, cow-dung cake, soap in `piece`.

Price range: ~Rs 4 (sugarcane/kg) to Rs 2,50,000 (saffron/kg).

## Configuration & Deployment

- Live on Render: https://farmer-api-ooi2.onrender.com/ (auto-deploys from the connected repo/branch).
- Env vars: `DATA_GOV_IN_API_KEY` (required for live; get free at data.gov.in → Dashboard → Generate API Key). Without it, API serves static fallback. Local: copy `.env.example` to `.env`.
- No DB, no auth — runs as-is. Source attribution required: data by DMI via `https://agmarknet.gov.in`.
- Prices: live = all-India modal average Rs/quintal ÷ 100 → Rs/kg (`source: live/cache`, with `arrival_date`, `markets_count`, `min/max_price_per_kg`, `matched_commodity`); non-mandi items (ghee, paneer, honey, milk, oils, pickles…) stay static (`source: static_fallback`). Force static with `?live=false`; filter live average with `?state=Punjab`.
- Production run: `uvicorn main:app --host 0.0.0.0 --port 8000` (add `--workers 4` as needed, or put behind nginx/Docker).
- Render start command (if configuring manually): `uvicorn main:app --host 0.0.0.0 --port $PORT`.
- Cache: 6h in-memory (`GET /cache/stats`, `POST /cache/refresh`).

## Limitations

- Live = wholesale daily modal average, not retail; converted to Rs/kg for local use.
- Mandi covers ~130-200 raw commodities daily; value-added goods stay static (Google News has no structured Rs/kg to parse — news links only, not implemented).
- `market_price_per_kg` field name is legacy — value is actually per `unit` (kg/litre/piece).
- Whole-word matching is English-only; Hindi/Bengali names are returned but not searchable.
- `ies → i` normalization can over-stem (e.g. `strawberries → strawberri`), still consistent on both sides so matches work.

## Roadmap

- [x] **Dynamic real-time prices** — Agmarknet via data.gov.in live average + static fallback, Rs/kg, `source/arrival_date/markets_count` fields.
- Search by Hindi/Bengali name.
- Query filters (`unit`, price range, category) + pagination.
- Move data to SQLite/Postgres or JSON/CSV + admin CRUD.
- Per-mandi breakdown endpoint (currently averaged).
- Tests (`pytest` + `httpx`/`TestClient`) and Dockerfile.

## License

No license file yet. Add one (e.g. MIT) if you plan to publish.
