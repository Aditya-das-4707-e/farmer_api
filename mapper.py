"""Map local product names -> govt Agmarknet commodity candidates.

Strategy:
  1. EXPLICIT_MAP for cases where naive Title-case fails
     (rice variants, wheat flours, typos like Mashrooms/Cucumbar, etc.)
  2. Heuristic: Full Title + last-word Title (green cabbage -> Cabbage,
     red onion -> Onion, alphonso mango -> Mango).
  3. If nothing matches at API level (0 records), caller falls back to static price.

Govt commodity strings must be EXACT (e.g. 'Bajra(Pearl Millet/Cumbu)',
'Barley(Jau)', 'Cucumbar(Kheera)'). Filters are case-sensitive lowercase key:
filters[commodity]=Onion works, filters[Commodity]=Onion returns 0.
"""
from typing import List

# normalized (lower, stripped) product -> ordered govt candidates
EXPLICIT_MAP = {
    # rice / paddy
    "rice": ["Rice", "Paddy(Common)"],
    "basmati rice": ["Paddy(Basmati)", "Rice"],
    "non-basmati rice": ["Rice", "Paddy(Common)"],
    "black rice": ["Rice"],
    "mushk budji rice": ["Rice"],
    "katarni rice": ["Rice"],
    "marcha rice": ["Rice"],
    "paddy": ["Paddy(Common)", "Rice"],
    # wheat + flours (no separate govt flour series -> Wheat)
    "wheat": ["Wheat"],
    "organic wheat": ["Wheat"],
    "stone-ground whole wheat flour": ["Wheat"],
    "chakki atta": ["Wheat"],
    "multi-grain flour": ["Wheat"],
    "rice flour": ["Rice"],
    "maida": ["Wheat"],
    "suji": ["Wheat"],
    "besan": ["Bengal Gram(Gram)(Whole)", "Gram Raw(Chholia)"],
    # maize / corn (govt has 'Sweet Corn ' with trailing space; API trims? try both)
    "maize": ["Maize"],
    "sweet corn": ["Sweet Corn", "Sweet Corn ", "Maize"],
    "baby corn": ["Baby Corn", "Maize"],
    # millets / cereals
    "barley": ["Barley(Jau)"],
    "jowar": ["Jowar(Sorghum)"],
    "bajra": ["Bajra(Pearl Millet/Cumbu)"],
    "ragi": ["Ragi(Finger Millet)"],
    # pulses
    "chana": ["Bengal Gram(Gram)(Whole)"],
    "kabuli chana": ["Bengal Gram(Gram)(Whole)", "Gram Raw(Chholia)"],
    "chickpeas": ["Bengal Gram(Gram)(Whole)"],
    "white peas": ["Peas(Dry)", "Green Peas"],
    "pigeon pea": ["Red gram/Arhar/Tur(whole)"],
    "arhar dal": ["Red gram/Arhar/Tur(whole)"],
    "toor dal": ["Red gram/Arhar/Tur(whole)"],
    "green gram": ["Green Gram(Moong)(Whole)"],
    "moong dal": ["Green Gram(Moong)(Whole)"],
    "black gram": ["Black Gram Dal(Urd Dal)"],
    "urad dal": ["Black Gram Dal(Urd Dal)"],
    "cowpeas": ["Cowpea(Veg)"],
    "lobia": ["Cowpea(Veg)"],
    "rajma": ["Indian Beans(Seam)", "Field Bean(Anumulu)"],
    "cluster beans": ["Cluster beans"],
    # oilseeds
    "soybean": ["Soyabean"],
    "soy oil": ["Soyabean"],
    "mustard": ["Mustard"],
    "mustard seeds": ["Mustard"],
    "yellow mustard": ["Mustard"],
    "black sarson": ["Mustard"],
    "groundnut": ["Groundnut"],
    "peanut": ["Groundnut"],
    "cold-pressed groundnut oil": ["Groundnut"],
    "sesame seeds": ["Sesame Seeds", "Sesame"],
    "sesame oil": ["Sesame Seeds", "Sesame"],
    "linseed": ["Linseed"],
    "linseed oil": ["Linseed"],
    "castor seeds": ["Castor Seeds", "Castor"],
    "cottonseeds": ["Cotton"],
    # fibres / plantation
    "cotton": ["Cotton"],
    "raw cotton": ["Cotton"],
    "cotton lint": ["Cotton"],
    "sugarcane": ["Sugarcane"],
    "organic sugarcane": ["Sugarcane"],
    "tobacco leaves": ["Tobacco"],
    "bidi tobacco leaves": ["Tobacco"],
    "betel leaves": ["Betal Leaves"],
    "areca nut": ["Arecanut", "Areca Nut"],
    "betel nut": ["Arecanut", "Areca Nut"],
    # vegetables (typos / bracket names)
    "bhindi": ["Bhindi(Ladies Finger)"],
    "okra": ["Bhindi(Ladies Finger)"],
    "cucumber": ["Cucumbar(Kheera)"],
    "colocasia": ["Colacasia"],
    "arbi": ["Colacasia"],
    "elephant foot yam": ["Elephant Yam(Suran)/Amorphophallus"],
    "bottle gourd": ["Bottle gourd"],
    "bitter gourd": ["Bitter gourd"],
    "ridge gourd": ["Ridgeguard(Tori)", "Ridge Gourd(Permal/Hybrid Gourd)"],
    "sponge gourd": ["Sponge gourd"],
    "pointed gourd": ["Pointed gourd(Parval)"],
    "parwal": ["Pointed gourd(Parval)"],
    "round gourd": ["Tinda"],
    "tinda": ["Tinda"],
    "ash gourd": ["Ashgourd"],
    "snake gourd": ["Snakeguard"],
    "snakeguard": ["Snakeguard"],
    "pumpkin": ["Pumpkin"],
    "brinjal": ["Brinjal"],
    "cabbage": ["Cabbage"],
    "green cabbage": ["Cabbage"],
    "red cabbage": ["Cabbage"],
    "cauliflower": ["Cauliflower"],
    "capsicum": ["Capsicum", "Chilly Capsicum"],
    "green chilli": ["Green Chilli"],
    "chilli": ["Chili Red", "Dry Chillies", "Green Chilli"],
    "dry red chilli": ["Dry Chillies", "Chili Red"],
    "red chilli powder": ["Dry Chillies", "Chili Red"],
    "guntur chilli": ["Dry Chillies", "Chili Red"],
    "byadgi chilli": ["Dry Chillies", "Chili Red"],
    "coriander leaves": ["Coriander(Leaves)"],
    "coriander seeds": ["Coriander(Leaves)", "Coriander Seed"],
    "mint leaves": ["Mint(Pudina)"],
    "fenugreek leaves": ["Methi Leaves", "Fenugreek"],
    "methi": ["Methi Leaves", "Fenugreek"],
    "amaranthus leaves": ["Amaranthus"],
    "spinach": ["Spinach"],
    "radish": ["Raddish"],
    "beetroot": ["Beetroot"],
    "carrot": ["Carrot"],
    "turnip": ["Turnip"],
    "sweet potato": ["Sweet Potato"],
    "tapioca": ["Tapioca"],
    "potato": ["Potato"],
    "onion": ["Onion"],
    "white onion": ["Onion"],
    "red onion": ["Onion"],
    "spring onion": ["Onion Green"],
    "garlic": ["Garlic"],
    "ginger": ["Ginger(Green)"],
    "dry ginger": ["Ginger(Dry)", "Ginger(Green)"],
    "sonth": ["Ginger(Dry)"],
    "tomato": ["Tomato"],
    "drumstick": ["Drumstick"],
    "moringa": ["Drumstick"],
    "green peas": ["Green Peas"],
    "french beans": ["French Beans(Frasbean)", "Beans"],
    "beans": ["Beans"],
    "mushroom": ["Mashrooms"],
    "button mushroom": ["Mashrooms"],
    "oyster mushroom": ["Mashrooms"],
    "shiitake mushroom": ["Mashrooms"],
    "milky mushroom": ["Mashrooms"],
    # fruits
    "mango": ["Mango", "Mango(Raw-Ripe)"],
    "alphonso mango": ["Mango", "Mango(Raw-Ripe)"],
    "dasheri mango": ["Mango", "Mango(Raw-Ripe)"],
    "langra mango": ["Mango", "Mango(Raw-Ripe)"],
    "chausa mango": ["Mango", "Mango(Raw-Ripe)"],
    "kesar mango": ["Mango", "Mango(Raw-Ripe)"],
    "kesar": ["Mango", "Saffron"],
    "banana": ["Banana", "Banana - Green"],
    "cavendish banana": ["Banana"],
    "robusta banana": ["Banana"],
    "nendran banana": ["Banana"],
    "elakki banana": ["Banana"],
    "red banana": ["Banana"],
    "apple": ["Apple"],
    "green apple": ["Apple"],
    "valencia orange": ["Orange"],
    "nagpur orange": ["Orange"],
    "orange": ["Orange"],
    "kinnow": ["Orange", "Kinnow"],
    "mosambi": ["Mousambi(Sweet Lime)"],
    "sweet lime": ["Mousambi(Sweet Lime)"],
    "lemon": ["Lemon"],
    "lime": ["Lime", "Lemon"],
    "lime pickle": ["Lime", "Lemon"],
    "pomegranate": ["Pomegranate"],
    "anar": ["Pomegranate"],
    "papaya": ["Papaya", "Papaya(Raw)"],
    "watermelon": ["Water Melon"],
    "muskmelon": ["Karbuja(Musk Melon)"],
    "pineapple": ["Pineapple"],
    "grapes": ["Grapes"],
    "green grapes": ["Grapes"],
    "black grapes": ["Grapes"],
    "red globe grapes": ["Grapes"],
    "guava": ["Guava"],
    "red guava": ["Guava"],
    "white guava": ["Guava"],
    "jackfruit": ["Jack Fruit(Ripe)"],
    "custard apple": ["Custard Apple(Sharifa)"],
    "sitafal": ["Custard Apple(Sharifa)", "Seetapal"],
    "fig": ["Fig(Anjura/Anjeer)"],
    "anjeer": ["Fig(Anjura/Anjeer)"],
    "sapota": ["Chikoos(Sapota)"],
    "chiku": ["Chikoos(Sapota)"],
    "coconut": ["Coconut", "Tender Coconut"],
    "tender coconut": ["Tender Coconut"],
    # spices / others with govt coverage
    "haldi": ["Turmeric"],
    "turmeric": ["Turmeric"],
    "tamarind": ["Tamarind Fruit"],
    "amla": ["Amla(Nelli Kai)"],
    "indian gooseberry": ["Amla(Nelli Kai)"],
    "mentha leaves": ["Mentha Oil", "Mint(Pudina)"],
    "mint oil": ["Mentha Oil"],
    "jaggery": ["Gur(Jaggery)"],
    "gur": ["Gur(Jaggery)"],
    "jaggery powder": ["Gur(Jaggery)"],
    # flowers
    "marigold": ["Marigold(Calcutta)"],
    "genda": ["Marigold(Calcutta)"],
    "marigold loose flower": ["Marigold(Calcutta)"],
    "jasmine": ["Jasmine"],
    "mogra": ["Jasmine"],
    "jasmine string": ["Jasmine"],
    "local rose": ["Rose(Local)"],
    "rose petal": ["Rose(Local)"],
    # animal / fish with limited govt rows
    "fish": ["Fish"],
    "rohu fish": ["Fish"],
    "catla fish": ["Fish"],
    "crab": ["Crab"],
    # everything else (milk, eggs, meat, ghee, paneer, oils, pickles, honey,
    # silk, manure, etc.) intentionally NOT mapped -> static_fallback
}


def _title(s: str) -> str:
    return " ".join(w[:1].upper() + w[1:] if w else w for w in s.strip().split())


def candidates_for(product_name: str) -> List[str]:
    """Ordered govt commodity candidates for a local product name."""
    key = product_name.strip().lower()
    if key in EXPLICIT_MAP:
        return list(EXPLICIT_MAP[key])
    cands: List[str] = []
    full = _title(product_name)
    if full:
        cands.append(full)
    parts = product_name.strip().split()
    if len(parts) > 1:
        last = _title(parts[-1])
        # crude singular: tomatoes->tomato, onions->onion, potatoes->potato
        singular = last
        low = last.lower()
        if low.endswith("oes"):
            singular = last[:-2]  # potatoes -> potato
        elif low.endswith("ies"):
            singular = last[:-3] + "y"  # berries -> berry
        elif low.endswith("s") and not low.endswith("ss") and len(low) > 3:
            singular = last[:-1]
        cands.append(singular)
        if singular != last:
            cands.append(last)
    # de-dupe preserve order
    seen = set()
    out = []
    for c in cands:
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out
