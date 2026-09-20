import re
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(
    title="Indian Market Price API",
    description="Search product name, get general market price. Example: /products/?name=rice. Plural-tolerant: potato/potatos/potatoes all work.",
    version="3.0.0",
)

# ---------------- Model: market price only (no farmer) ----------------

class ProductPrice(BaseModel):
    id: int
    product_name: str
    hindi_name: Optional[str] = None
    bengali_name: Optional[str] = None
    market_price_per_kg: float  # INR per unit - general market rate
    unit: str = "kg"
    currency: str = "INR"
    market_price: Optional[str] = None  # e.g. "Rs 28 per kg"


# ---------------- Data: (name, hindi, bengali, price, unit) ----------------
# One market price per product. New bulk items use None for hindi/bengali.

RAW_PRODUCTS = [
    ('rice', 'चावल', 'চাল', 65.0, 'kg'),
    ('wheat', 'गेहूं', 'গম', 38.0, 'kg'),
    ('sugarcane', 'गन्ना', 'আখ', 4.0, 'kg'),
    ('cotton', 'कपास', 'তুলা', 75.0, 'kg'),
    ('maize', 'मक्का', 'ভুট্টা', 30.0, 'kg'),
    ('soybean', 'सोयाबीन', 'সয়াবিন', 55.0, 'kg'),
    ('mustard', 'सरसों', 'সরষে', 65.0, 'kg'),
    ('groundnut', 'मूंगफली', 'চিনাবাদাম', 110.0, 'kg'),
    ('onion', 'प्याज', 'পেঁয়াজ', 40.0, 'kg'),
    ('potato', 'आलू', 'আলু', 28.0, 'kg'),
    ('tomato', 'टमाटर', 'টমেটো', 35.0, 'kg'),
    ('mango', 'आम', 'আম', 140.0, 'kg'),
    ('banana', 'केला', 'কলা', 50.0, 'kg'),
    ('turmeric', 'हल्दी', 'হলুদ', 170.0, 'kg'),
    ('chilli', 'मिर्च', 'লঙ্কা', 200.0, 'kg'),
    ('tea', 'चाय', 'চা', 280.0, 'kg'),
    ('paddy', 'धान', 'ধান', 32.0, 'kg'),
    ('basmati rice', 'बासमती चावल', 'বাসমতী চাল', 110.0, 'kg'),
    ('non-basmati rice', 'नॉन-बासमती चावल', 'নন-বাসমতী চাল', 60.0, 'kg'),
    ('black rice', 'काला चावल', 'কালো চাল', 145.0, 'kg'),
    ('mushk budji rice', 'मुश्क बुदजी चावल', 'মুশক বুদজি চাল', 135.0, 'kg'),
    ('katarni rice', 'कतरनी चावल', 'কাতারনি চাল', 95.0, 'kg'),
    ('marcha rice', 'मरचा चावल', 'মারচা চাল', 88.0, 'kg'),
    ('organic wheat', 'जैविक गेहूं', 'জৈব গম', 55.0, 'kg'),
    ('sweet corn', 'मीठी मक्का', 'মিষ্টি ভুট্টা', 45.0, 'kg'),
    ('barley', 'जौ', 'যব', 45.0, 'kg'),
    ('oats', 'जई', 'ওটস', 120.0, 'kg'),
    ('rye', 'राई', 'রাই', 70.0, 'kg'),
    ('jowar', 'ज्वार', 'জোয়ার', 52.0, 'kg'),
    ('bajra', 'बाजरा', 'বাজরা', 46.0, 'kg'),
    ('ragi', 'रागी', 'রাগি', 58.0, 'kg'),
    ('foxtail millet', 'कंगनी', 'কাঙনি', 72.0, 'kg'),
    ('little millet', 'कुटकी', 'সামা', 76.0, 'kg'),
    ('barnyard millet', 'सांवा', 'সাঁওয়া', 82.0, 'kg'),
    ('proso millet', 'चेना', 'চিনা', 70.0, 'kg'),
    ('kodo millet', 'कोदो', 'কোদো', 75.0, 'kg'),
    ('browntop millet', 'ब्राउनटॉप मिलेट', 'ব্রাউনটপ মিলেট', 92.0, 'kg'),
    ('amaranth seed', 'चौलाई बीज', 'আমরান্থ বীজ', 125.0, 'kg'),
    ('buckwheat', 'कुट्टू', 'বাকহুইট', 115.0, 'kg'),
    ('chana', 'चना', 'ছোলা', 85.0, 'kg'),
    ('kabuli chana', 'काबुली चना', 'কাবুলি ছোলা', 112.0, 'kg'),
    ('white peas', 'सफेद मटर', 'সাদা মটর', 92.0, 'kg'),
    ('pigeon pea', 'अरहर', 'অড়হর', 132.0, 'kg'),
    ('arhar dal', 'अरहर दाल', 'অড়হর ডাল', 152.0, 'kg'),
    ('toor dal', 'तूर दाल', 'তুর ডাল', 152.0, 'kg'),
    ('green gram', 'हरी मूंग', 'সবুজ মুগ', 126.0, 'kg'),
    ('moong dal', 'मूंग दाल', 'মুগ ডাল', 136.0, 'kg'),
    ('black gram', 'उड़द', 'বিউলি', 132.0, 'kg'),
    ('urad dal', 'उड़द दाल', 'বিউলির ডাল', 138.0, 'kg'),
    ('lentils', 'मसूर', 'মসুর', 122.0, 'kg'),
    ('masoor dal', 'मसूर दाल', 'মসুর ডাল', 112.0, 'kg'),
    ('horse gram', 'कुलथी', 'কুলথি', 92.0, 'kg'),
    ('lobia', 'लोबिया', 'লোবিয়া', 112.0, 'kg'),
    ('moth bean', 'मोठ', 'মথ বিন', 108.0, 'kg'),
    ('khesari dal', 'खेसारी दाल', 'খেসারি ডাল', 82.0, 'kg'),
    ('rajma', 'राजमा', 'রাজমা', 142.0, 'kg'),
    ('cowpeas', 'चवला', 'বরবটি', 116.0, 'kg'),
    ('chickpeas', 'चना', 'ছোলা', 96.0, 'kg'),
    ('cluster beans', 'ग्वार फली', 'গুয়ার ফলি', 62.0, 'kg'),
    ('white onion', 'सफेद प्याज', 'সাদা পেঁয়াজ', 42.0, 'kg'),
    ('red onion', 'लाल प्याज', 'লাল পেঁয়াজ', 43.0, 'kg'),
    ('garlic', 'लहसुन', 'রসুন', 160.0, 'kg'),
    ('ginger', 'अदरक', 'আদা', 90.0, 'kg'),
    ('cauliflower', 'फूलगोभी', 'ফুলকপি', 32.0, 'kg'),
    ('broccoli', 'ब्रोकली', 'ব্রকলি', 85.0, 'kg'),
    ('green cabbage', 'हरी पत्तागोभी', 'সবুজ বাঁধাকপি', 28.0, 'kg'),
    ('red cabbage', 'लाल पत्तागोभी', 'লাল বাঁধাকপি', 38.0, 'kg'),
    ('brinjal', 'बैंगन', 'বেগুন', 38.0, 'kg'),
    ('okra', 'भिंडी', 'ঢেঁড়স', 45.0, 'kg'),
    ('bhindi', 'भिंडी', 'ঢেঁড়স', 45.0, 'kg'),
    ('green chilli', 'हरी मिर्च', 'কাঁচা লঙ্কা', 90.0, 'kg'),
    ('capsicum', 'शिमला मिर्च', 'ক্যাপসিকাম', 70.0, 'kg'),
    ('red bell pepper', 'लाल शिमला मिर्च', 'লাল ক্যাপসিকাম', 120.0, 'kg'),
    ('yellow bell pepper', 'पीली शिमला मिर्च', 'হলুদ ক্যাপসিকাম', 125.0, 'kg'),
    ('zucchini', 'जुकीनी', 'জুকিনি', 95.0, 'kg'),
    ('cucumber', 'खीरा', 'শসা', 30.0, 'kg'),
    ('pumpkin', 'कद्दू', 'কুমড়ো', 28.0, 'kg'),
    ('bottle gourd', 'लौकी', 'লাউ', 30.0, 'kg'),
    ('bitter gourd', 'करेला', 'করলা', 42.0, 'kg'),
    ('ridge gourd', 'तोरई', 'ঝিঙে', 40.0, 'kg'),
    ('sponge gourd', 'गिलकी', 'ধুঁধুল', 38.0, 'kg'),
    ('pointed gourd', 'परवल', 'পটল', 45.0, 'kg'),
    ('parwal', 'परवल', 'পটল', 48.0, 'kg'),
    ('round gourd', 'टिंडा', 'টিন্ডা', 35.0, 'kg'),
    ('tinda', 'टिंडा', 'টিন্ডা', 35.0, 'kg'),
    ('ash gourd', 'पेठा', 'চালকুমড়ো', 28.0, 'kg'),
    ('snake gourd', 'चिचिंडा', 'চিচিঙ্গা', 36.0, 'kg'),
    ('beetroot', 'चुकंदर', 'বিট', 45.0, 'kg'),
    ('carrot', 'गाजर', 'গাজর', 50.0, 'kg'),
    ('radish', 'मूली', 'মুলো', 32.0, 'kg'),
    ('turnip', 'शलजम', 'শালগম', 35.0, 'kg'),
    ('sweet potato', 'शकरकंद', 'মিষ্টি আলু', 45.0, 'kg'),
    ('colocasia', 'अरबी', 'কচু', 55.0, 'kg'),
    ('arbi', 'अरबी', 'কচু', 55.0, 'kg'),
    ('elephant foot yam', 'जिमीकंद', 'ওল', 48.0, 'kg'),
    ('tapioca', 'टैपिओका', 'ট্যাপিওকা', 32.0, 'kg'),
    ('spinach', 'पालक', 'পালং শাক', 30.0, 'kg'),
    ('fenugreek leaves', 'मेथी पत्ते', 'মেথি পাতা', 35.0, 'kg'),
    ('methi', 'मेथी', 'মেথি', 35.0, 'kg'),
    ('amaranthus leaves', 'चौलाई साग', 'চৌলাই শাক', 32.0, 'kg'),
    ('mustard greens', 'सरसों साग', 'সরষে শাক', 30.0, 'kg'),
    ('bathua', 'बथुआ', 'বথুয়া', 28.0, 'kg'),
    ('coriander leaves', 'धनिया पत्ते', 'ধনে পাতা', 40.0, 'kg'),
    ('mint leaves', 'पुदीना पत्ते', 'পুদিনা পাতা', 45.0, 'kg'),
    ('curry leaves', 'करी पत्ते', 'কারি পাতা', 60.0, 'kg'),
    ('drumstick', 'सहजन', 'সজনে', 55.0, 'kg'),
    ('moringa', 'मोरिंगा', 'মোরিঙ্গা', 60.0, 'kg'),
    ('green peas', 'हरी मटर', 'সবুজ মটর', 75.0, 'kg'),
    ('french beans', 'फ्रेंच बीन्स', 'ফ্রেঞ্চ বিন', 70.0, 'kg'),
    ('runner beans', 'रनर बीन्स', 'রানার বিন', 75.0, 'kg'),
    ('baby corn', 'बेबी कॉर्न', 'বেবি কর্ন', 85.0, 'kg'),
    ('spring onion', 'हरा प्याज़', 'পেঁয়াজকলি', 45.0, 'kg'),
    ('leek', 'लीक', 'লিক', 90.0, 'kg'),
    ('celery', 'सेलेरी', 'সেলারি', 95.0, 'kg'),
    ('lettuce', 'सलाद पत्ता', 'লেটুস', 80.0, 'kg'),
    ('microgreens', 'माइक्रोग्रीन्स', 'মাইক্রোগ্রিনস', 250.0, 'kg'),
    ('button mushroom', 'बटन मशरूम', 'বোতাম মাশরুম', 160.0, 'kg'),
    ('oyster mushroom', 'ऑयस्टर मशरूम', 'অয়েস্টার মাশরুম', 180.0, 'kg'),
    ('shiitake mushroom', 'शिटाके मशरूम', 'শিটাকে মাশরুম', 450.0, 'kg'),
    ('milky mushroom', 'मिल्की मशरूम', 'মিল্কি মাশরুম', 170.0, 'kg'),
    ('alphonso mango', 'अलफांसो आम', 'আলফানসো আম', 250.0, 'kg'),
    ('dasheri mango', 'दशहरी आम', 'দশহরি আম', 140.0, 'kg'),
    ('langra mango', 'लंगड़ा आम', 'ল্যাংড়া আম', 130.0, 'kg'),
    ('chausa mango', 'चौसा आम', 'চৌসা আম', 150.0, 'kg'),
    ('kesar mango', 'केसर आम', 'কেসর আম', 160.0, 'kg'),
    ('cavendish banana', 'कैवेंडिश केला', 'ক্যাভেন্ডিশ কলা', 55.0, 'kg'),
    ('robusta banana', 'रोबस्टा केला', 'রোবস্টা কলা', 50.0, 'kg'),
    ('nendran banana', 'नेंद्रन केला', 'নেন্দ্রন কলা', 75.0, 'kg'),
    ('elakki banana', 'इलक्की केला', 'এলাক্কি কলা', 80.0, 'kg'),
    ('red banana', 'लाल केला', 'লাল কলা', 85.0, 'kg'),
    ('apple', 'सेब', 'আপেল', 160.0, 'kg'),
    ('green apple', 'हरा सेब', 'সবুজ আপেল', 180.0, 'kg'),
    ('valencia orange', 'वालेंसिया संतरा', 'ভ্যালেন্সিয়া কমলা', 120.0, 'kg'),
    ('nagpur orange', 'नागपुर संतरा', 'নাগপুর কমলা', 90.0, 'kg'),
    ('kinnow', 'किन्नू', 'কিন্নু', 80.0, 'kg'),
    ('mosambi', 'मौसंबी', 'মৌসম্বি', 75.0, 'kg'),
    ('sweet lime', 'मीठा नींबू', 'মিষ্টি লেবু', 70.0, 'kg'),
    ('lemon', 'नींबू', 'লেবু', 90.0, 'kg'),
    ('lime', 'कागज़ी नींबू', 'কাগজি লেবু', 85.0, 'kg'),
    ('pomegranate', 'अनार', 'ডালিম', 140.0, 'kg'),
    ('anar', 'अनार', 'আনার', 140.0, 'kg'),
    ('red guava', 'लाल अमरूद', 'লাল পেয়ারা', 70.0, 'kg'),
    ('white guava', 'सफेद अमरूद', 'সাদা পেয়ারা', 65.0, 'kg'),
    ('papaya', 'पपीता', 'পেঁপে', 60.0, 'kg'),
    ('watermelon', 'तरबूज', 'তরমুজ', 30.0, 'kg'),
    ('muskmelon', 'खरबूजा', 'খরমুজ', 55.0, 'kg'),
    ('pineapple', 'अनानास', 'আনারস', 70.0, 'kg'),
    ('grapes', 'अंगूर', 'আঙুর', 90.0, 'kg'),
    ('green grapes', 'हरे अंगूर', 'সবুজ আঙুর', 95.0, 'kg'),
    ('black grapes', 'काले अंगूर', 'কালো আঙুর', 110.0, 'kg'),
    ('red globe grapes', 'रेड ग्लोब अंगूर', 'রেড গ্লোব আঙুর', 130.0, 'kg'),
    ('litchi', 'लीची', 'লিচু', 150.0, 'kg'),
    ('jackfruit', 'कटहल', 'কাঁঠাল', 70.0, 'kg'),
    ('custard apple', 'सीताफल', 'আতা', 110.0, 'kg'),
    ('sitafal', 'सीताफल', 'সীতাফল', 110.0, 'kg'),
    ('wood apple', 'कैथ', 'কদবেল', 80.0, 'kg'),
    ('bael', 'बेल', 'বেল', 80.0, 'kg'),
    ('jambul', 'जामुन', 'জাম', 120.0, 'kg'),
    ('jamun', 'जामुन', 'জামুন', 120.0, 'kg'),
    ('fig', 'अंजीर', 'আঞ্জির', 220.0, 'kg'),
    ('anjeer', 'अंजीर', 'আঞ্জির', 220.0, 'kg'),
    ('sapota', 'चीकू', 'সবেদা', 90.0, 'kg'),
    ('chiku', 'चीकू', 'চিকু', 90.0, 'kg'),
    ('plum', 'आलूबुखारा', 'আলুবোখারা', 160.0, 'kg'),
    ('peach', 'आड़ू', 'পীচ', 180.0, 'kg'),
    ('pear', 'नाशपाती', 'নাশপাতি', 150.0, 'kg'),
    ('apricot', 'खुबानी', 'খুবানি', 220.0, 'kg'),
    ('cherry', 'चेरी', 'চেরি', 320.0, 'kg'),
    ('strawberry', 'स्ट्रॉबेरी', 'স্ট্রবেরি', 280.0, 'kg'),
    ('blueberry', 'ब्लूबेरी', 'ব্লুবেরি', 450.0, 'kg'),
    ('raspberry', 'रसभरी', 'রাসবেরি', 480.0, 'kg'),
    ('cape gooseberry', 'केप गूजबेरी', 'টেপারি ফল', 180.0, 'kg'),
    ('rasbhari', 'रसभरी', 'রসভরি', 180.0, 'kg'),
    ('dragon fruit', 'ड्रैगन फ्रूट', 'ড্রাগন ফল', 160.0, 'kg'),
    ('pitaya', 'पिताया', 'পিতায়া', 160.0, 'kg'),
    ('passion fruit', 'पैशन फ्रूट', 'প্যাশন ফল', 180.0, 'kg'),
    ('kiwi', 'कीवी', 'কিউই', 200.0, 'kg'),
    ('star fruit', 'कमरख', 'কামরাঙা', 120.0, 'kg'),
    ('carambola', 'कमरख', 'কামরাঙা', 120.0, 'kg'),
    ('avocado', 'एवोकाडो', 'অ্যাভোকাডো', 220.0, 'kg'),
    ('mustard seeds', 'सरसों के बीज', 'সরষের বীজ', 68.0, 'kg'),
    ('yellow mustard', 'पीली सरसों', 'হলুদ সরষে', 70.0, 'kg'),
    ('black sarson', 'काली सरसों', 'কালো সরষে', 68.0, 'kg'),
    ('peanut', 'मूंगफली', 'চিনাবাদাম', 105.0, 'kg'),
    ('sunflower seeds', 'सूरजमुखी के बीज', 'সূর্যমুখী বীজ', 110.0, 'kg'),
    ('sesame seeds', 'तिल के बीज', 'তিল বীজ', 140.0, 'kg'),
    ('white til', 'सफेद तिल', 'সাদা তিল', 145.0, 'kg'),
    ('black til', 'काला तिल', 'কালো তিল', 150.0, 'kg'),
    ('safflower seeds', 'कुसुम के बीज', 'কুসুম বীজ', 95.0, 'kg'),
    ('niger seeds', 'रामतिल', 'নাইজার বীজ', 90.0, 'kg'),
    ('linseed', 'अलसी', 'তিসি', 110.0, 'kg'),
    ('flaxseeds', 'अलसी के बीज', 'তিসি বীজ', 115.0, 'kg'),
    ('castor seeds', 'अरंडी के बीज', 'রেড়ির বীজ', 85.0, 'kg'),
    ('cottonseeds', 'कपास के बीज', 'তুলোর বীজ', 70.0, 'kg'),
    ('coconut', 'नारियल', 'নারকেল', 45.0, 'kg'),
    ('raw copra', 'कच्चा खोपरा', 'কাঁচা খোপরা', 150.0, 'kg'),
    ('milling copra', 'मिलिंग खोपरा', 'মিলিং খোপরা', 160.0, 'kg'),
    ('oil palm fruit', 'ऑयल पाम फल', 'অয়েল পাম ফল', 30.0, 'kg'),
    ('neem seeds', 'नीम के बीज', 'নিম বীজ', 45.0, 'kg'),
    ('organic sugarcane', 'जैविक गन्ना', 'জৈব আখ', 5.0, 'kg'),
    ('cotton lint', 'कपास रेशा', 'তুলোর আঁশ', 90.0, 'kg'),
    ('raw cotton', 'कच्चा कपास', 'কাঁচা তুলো', 80.0, 'kg'),
    ('tossa jute', 'तोसा पटसन', 'তোসা পাট', 65.0, 'kg'),
    ('white jute', 'सफेद पटसन', 'সাদা পাট', 62.0, 'kg'),
    ('mesta', 'मेस्ता', 'মেস্তা', 60.0, 'kg'),
    ('sunnhemp', 'सनई', 'শণ', 58.0, 'kg'),
    ('rubber sheets', 'रबर शीट', 'রাবার শীট', 180.0, 'kg'),
    ('latex', 'लेटेक्स', 'ল্যাটেক্স', 160.0, 'kg'),
    ('ctcm tea leaves', 'सीटीसी चाय पत्ती', 'সিটিসি চা পাতা', 300.0, 'kg'),
    ('orthodox tea leaves', 'ऑर्थोडॉक्स चाय पत्ती', 'অর্থোডক্স চা পাতা', 450.0, 'kg'),
    ('green tea leaves', 'ग्रीन टी पत्ती', 'গ্রিন টি পাতা', 500.0, 'kg'),
    ('assam tea', 'असम चाय', 'আসাম চা', 350.0, 'kg'),
    ('darjeeling tea', 'दार्जिलिंग चाय', 'দার্জিলিং চা', 600.0, 'kg'),
    ('arabica coffee beans', 'अरेबिका कॉफी बीन्स', 'আরাবিকা কফি বীজ', 650.0, 'kg'),
    ('robusta coffee beans', 'रोबस्टा कॉफी बीन्स', 'রোবস্টা কফি বীজ', 480.0, 'kg'),
    ('cocoa pods', 'कोको फली', 'কোকো ফল', 250.0, 'kg'),
    ('raw cocoa beans', 'कच्चा कोको बीन्स', 'কাঁচা কোকো বীজ', 400.0, 'kg'),
    ('areca nut', 'सुपारी', 'সুপারি', 280.0, 'kg'),
    ('betel nut', 'सुपारी', 'সুপারি', 280.0, 'kg'),
    ('betel leaves', 'पान के पत्ते', 'পান পাতা', 40.0, 'kg'),
    ('cashew', 'काजू', 'কাজু', 750.0, 'kg'),
    ('raw cashew nut with shell', 'छिलके सहित कच्चा काजू', 'খোসাসহ কাঁচা কাজু', 450.0, 'kg'),
    ('tobacco leaves', 'तंबाकू के पत्ते', 'তামাক পাতা', 220.0, 'kg'),
    ('bidi tobacco leaves', 'बीड़ी तंबाकू पत्ते', 'বিড়ি তামাক পাতা', 200.0, 'kg'),
    ('haldi', 'हल्दी', 'হলুদ', 170.0, 'kg'),
    ('dry ginger', 'सूखी अदरक', 'শুকনো আদা', 320.0, 'kg'),
    ('sonth', 'सोंठ', 'শুঁঠ', 320.0, 'kg'),
    ('black pepper', 'काली मिर्च', 'কালো গোলমরিচ', 750.0, 'kg'),
    ('white pepper', 'सफेद मिर्च', 'সাদা গোলমরিচ', 850.0, 'kg'),
    ('red chilli powder', 'लाल मिर्च पाउडर', 'লাল লঙ্কা গুঁড়ো', 280.0, 'kg'),
    ('dry red chilli', 'सूखी लाल मिर्च', 'শুকনো লাল লঙ্কা', 250.0, 'kg'),
    ('byadgi chilli', 'ब्यादगी मिर्च', 'ব্যাদগি লঙ্কা', 300.0, 'kg'),
    ('guntur chilli', 'गुंटूर मिर्च', 'গুন্টুর লঙ্কা', 290.0, 'kg'),
    ('cumin seeds', 'जीरा', 'জিরা', 320.0, 'kg'),
    ('jeera', 'जीरा', 'জিরা', 320.0, 'kg'),
    ('coriander seeds', 'धनिया बीज', 'ধনে বীজ', 180.0, 'kg'),
    ('dhania', 'धनिया', 'ধনে', 180.0, 'kg'),
    ('fennel seeds', 'सौंफ', 'মৌরি', 220.0, 'kg'),
    ('saunf', 'सौंफ', 'মৌরি', 220.0, 'kg'),
    ('fenugreek seeds', 'मेथी दाना', 'মেথি দানা', 140.0, 'kg'),
    ('methi dana', 'मेथी दाना', 'মেথি দানা', 140.0, 'kg'),
    ('green cardamom', 'छोटी इलायची', 'ছোট এলাচ', 1400.0, 'kg'),
    ('choti elaichi', 'छोटी इलायची', 'ছোট এলাচ', 1400.0, 'kg'),
    ('black cardamom', 'बड़ी इलायची', 'বড় এলাচ', 1100.0, 'kg'),
    ('badi elaichi', 'बड़ी इलायची', 'বড় এলাচ', 1100.0, 'kg'),
    ('clove', 'लौंग', 'লবঙ্গ', 950.0, 'kg'),
    ('laung', 'लौंग', 'লবঙ্গ', 950.0, 'kg'),
    ('cinnamon sticks', 'दालचीनी', 'দারুচিনি', 600.0, 'kg'),
    ('dalchini', 'दालचीनी', 'দারুচিনি', 600.0, 'kg'),
    ('cassia', 'कैसिया', 'কাসিয়া', 550.0, 'kg'),
    ('mace', 'जावित्री', 'জৈত্রী', 1200.0, 'kg'),
    ('javitri', 'जावित्री', 'জৈত্রী', 1200.0, 'kg'),
    ('nutmeg', 'जायफल', 'জায়ফল', 800.0, 'kg'),
    ('jaiphal', 'जायफल', 'জায়ফল', 800.0, 'kg'),
    ('star anise', 'चक्र फूल', 'চক্র ফুল', 900.0, 'kg'),
    ('chakra phool', 'चक्र फूल', 'চক্র ফুল', 900.0, 'kg'),
    ('carom seeds', 'अजवाइन', 'জোয়ান', 220.0, 'kg'),
    ('ajwain', 'अजवाइन', 'জোয়ান', 220.0, 'kg'),
    ('kalonji', 'कलौंजी', 'কালোজিরা', 450.0, 'kg'),
    ('nigella seeds', 'कलौंजी', 'কালোজিরা', 450.0, 'kg'),
    ('mustard powder', 'सरसों पाउडर', 'সরষে গুঁড়ো', 180.0, 'kg'),
    ('tamarind', 'इमली', 'তেঁতুল', 130.0, 'kg'),
    ('dried mango powder', 'अमचूर', 'আমচুর', 280.0, 'kg'),
    ('amchur', 'अमचूर', 'আমচুর', 280.0, 'kg'),
    ('asafoetida', 'हींग', 'হিং', 1200.0, 'kg'),
    ('hing', 'हींग', 'হিং', 1200.0, 'kg'),
    ('poppy seeds', 'खसखस', 'পোস্তদানা', 850.0, 'kg'),
    ('khus khus', 'खसखस', 'পোস্তদানা', 850.0, 'kg'),
    ('saffron', 'केसर', 'জাফরান', 250000.0, 'kg'),
    ('kesar', 'केसर', 'জাফরান', 250000.0, 'kg'),
    ('mentha leaves', 'मेंथा पत्ती', 'মেন্থা পাতা', 60.0, 'kg'),
    ('mint oil', 'पुदीना तेल', 'পুদিনা তেল', 1200.0, 'litre'),
    ('aloe vera leaves', 'घृतकुमारी पत्ती', 'ঘৃতকুমারী পাতা', 35.0, 'kg'),
    ('ashwagandha roots', 'अश्वगंधा जड़', 'অশ্বগন্ধা মূল', 450.0, 'kg'),
    ('tulsi leaves', 'तुलसी पत्ती', 'তুলসী পাতা', 120.0, 'kg'),
    ('senna leaves', 'सनाय पत्ती', 'সোনাপাতা', 140.0, 'kg'),
    ('safed musli', 'सफेद मूसली', 'সফেদ মুসলি', 1200.0, 'kg'),
    ('sarpagandha', 'सर्पगंधा', 'সর্পগন্ধা', 380.0, 'kg'),
    ('lemongrass', 'लेमनग्रास', 'লেমনগ্রাস', 70.0, 'kg'),
    ('citronella', 'सिट्रोनेला', 'সিট্রোনেলা', 900.0, 'litre'),
    ('palmarosa', 'पामारोसा', 'পামারোসা', 950.0, 'litre'),
    ('stevia leaves', 'स्टीविया पत्ती', 'স্টেভিয়া পাতা', 300.0, 'kg'),
    ('amla', 'आंवला', 'আমলকী', 80.0, 'kg'),
    ('indian gooseberry', 'आंवला', 'আমলকী', 80.0, 'kg'),
    ('neem leaves', 'नीम पत्ती', 'নিম পাতা', 45.0, 'kg'),
    ('giloy', 'गिलोय', 'গিলয়', 180.0, 'kg'),
    ('arjuna bark', 'अर्जुन छाल', 'অর্জুন ছাল', 220.0, 'kg'),
    ('isabgol', 'इसबगोल', 'ইসবগুল', 350.0, 'kg'),
    ('psyllium husk', 'इसबगोल भूसी', 'ইসবগুলের ভুসি', 350.0, 'kg'),
    ('kalmegh', 'कालमेघ', 'কালমেঘ', 200.0, 'kg'),
    ('marigold', 'गेंदा', 'গাঁদা', 60.0, 'kg'),
    ('genda', 'गेंदा', 'গাঁদা', 60.0, 'kg'),
    ('local rose', 'देशी गुलाब', 'দেশি গোলাপ', 120.0, 'kg'),
    ('dutch rose', 'डच गुलाब', 'ডাচ গোলাপ', 250.0, 'kg'),
    ('jasmine', 'चमेली', 'জুঁই', 300.0, 'kg'),
    ('mogra', 'मोगरा', 'বেলফুল', 300.0, 'kg'),
    ('tuberose', 'रजनीगंधा', 'রজনীগন্ধা', 180.0, 'kg'),
    ('rajnigandha', 'रजनीगंधा', 'রজনীগন্ধা', 180.0, 'kg'),
    ('gladiolus', 'ग्लेडियोलस', 'গ্ল্যাডিওলাস', 160.0, 'kg'),
    ('chrysanthemum', 'गुलदाउदी', 'চন্দ্রমল্লিকা', 140.0, 'kg'),
    ('guldaudi', 'गुलदाउदी', 'চন্দ্রমল্লিকা', 140.0, 'kg'),
    ('carnation', 'कार्नेशन', 'কার্নেশন', 200.0, 'kg'),
    ('gerbera', 'जरबेरा', 'জারবেরা', 180.0, 'kg'),
    ('orchid', 'ऑर्किड', 'অর্কিড', 400.0, 'kg'),
    ('anthurium', 'एन्थुरियम', 'অ্যান্থুরিয়াম', 350.0, 'kg'),
    ('lily', 'लिली', 'লিলি', 220.0, 'kg'),
    ('marigold loose flower', 'गेंदा फूल', 'গাঁদা ফুল', 50.0, 'kg'),
    ('rose petal', 'गुलाब पंखुड़ी', 'গোলাপ পাপড়ি', 250.0, 'kg'),
    ('jasmine string', 'चमेली माला', 'জুঁই ফুলের মালা', 120.0, 'kg'),
    ('cow milk', 'गाय का दूध', 'গরুর দুধ', 60.0, 'litre'),
    ('a2 cow milk', 'ए2 गाय का दूध', 'এ২ গরুর দুধ', 85.0, 'litre'),
    ('buffalo milk', 'भैंस का दूध', 'মহিষের দুধ', 75.0, 'litre'),
    ('goat milk', 'बकरी का दूध', 'ছাগলের দুধ', 120.0, 'litre'),
    ('camel milk', 'ऊंट का दूध', 'উটের দুধ', 110.0, 'litre'),
    ('poultry egg', 'मुर्गी का अंडा', 'মুরগির ডিম', 8.0, 'piece'),
    ('duck egg', 'बत्तख का अंडा', 'হাঁসের ডিম', 15.0, 'piece'),
    ('broiler chicken', 'ब्रॉयलर चिकन', 'ব্রয়লার মুরগি', 180.0, 'kg'),
    ('country chicken', 'देशी चिकन', 'দেশি মুরগি', 350.0, 'kg'),
    ('kadaknath chicken', 'कड़कनाथ चिकन', 'কড়কনাথ মুরগি', 650.0, 'kg'),
    ('duck', 'बत्तख', 'হাঁস', 280.0, 'kg'),
    ('turkey', 'टर्की', 'টার্কি', 450.0, 'kg'),
    ('goat meat', 'बकरे का मांस', 'ছাগলের মাংস', 750.0, 'kg'),
    ('chevon', 'बकरे का मांस', 'ছাগলের মাংস', 750.0, 'kg'),
    ('sheep meat', 'भेड़ का मांस', 'ভেড়ার মাংস', 720.0, 'kg'),
    ('mutton', 'मटन', 'মাটন', 740.0, 'kg'),
    ('pork', 'सूअर का मांस', 'শুয়োরের মাংস', 380.0, 'kg'),
    ('rabbit meat', 'खरगोश का मांस', 'খরগোশের মাংস', 550.0, 'kg'),
    ('raw sheep wool', 'कच्ची भेड़ ऊन', 'কাঁচা ভেড়ার পশম', 250.0, 'kg'),
    ('raw animal hide', 'कच्ची जानवर की खाल', 'কাঁচা পশুর চামড়া', 180.0, 'kg'),
    ('cattle skin', 'मवेशी की खाल', 'গবাদি পশুর চামড়া', 200.0, 'kg'),
    ('rohu fish', 'रोहू मछली', 'রুই মাছ', 220.0, 'kg'),
    ('catla fish', 'कतला मछली', 'কাতলা মাছ', 210.0, 'kg'),
    ('mrigal fish', 'मृगल मछली', 'মৃগেল মাছ', 200.0, 'kg'),
    ('hilsa fish', 'हिल्सा मछली', 'ইলিশ মাছ', 1200.0, 'kg'),
    ('silver carp', 'सिल्वर कार्प मछली', 'সিলভার কার্প মাছ', 180.0, 'kg'),
    ('grass carp', 'ग्रास कार्प मछली', 'গ্রাস কার্প মাছ', 190.0, 'kg'),
    ('common carp', 'कॉमन कार्प मछली', 'কমন কার্প মাছ', 185.0, 'kg'),
    ('pangasius fish', 'पंगासियस मछली', 'পাঙ্গাস মাছ', 150.0, 'kg'),
    ('tilapia', 'तिलापिया मछली', 'তেলাপিয়া মাছ', 170.0, 'kg'),
    ('tiger prawn', 'बाघ झींगा', 'বাগদা চিংড়ি', 650.0, 'kg'),
    ('whiteleg shrimp', 'वैनामेई झींगा', 'ভ্যানামি চিংড়ি', 550.0, 'kg'),
    ('freshwater prawn', 'मीठे पानी का झींगा', 'মিঠা পানির চিংড়ি', 600.0, 'kg'),
    ('crab', 'केकड़ा', 'কাঁকড়া', 550.0, 'kg'),
    ('organic manure', 'जैविक खाद', 'জৈব সার', 12.0, 'kg'),
    ('vermicompost', 'केंचुआ खाद', 'কেঁচো সার', 15.0, 'kg'),
    ('cow dung cake', 'गोबर का उपला', 'ঘুঁটে', 10.0, 'piece'),
    ('panchagavya', 'पंचगव्य', 'পঞ্চগব্য', 150.0, 'litre'),
    ('raw honey', 'कच्चा शहद', 'কাঁচা মধু', 450.0, 'kg'),
    ('mustard honey', 'सरसों का शहद', 'সরষে মধু', 420.0, 'kg'),
    ('eucalyptus honey', 'नीलगिरी शहद', 'ইউক্যালিপটাস মধু', 480.0, 'kg'),
    ('multi-floral honey', 'बहुफूली शहद', 'বহুফুলের মধু', 460.0, 'kg'),
    ('forest honey', 'जंगली शहद', 'বনের মধু', 550.0, 'kg'),
    ('beeswax', 'मधुमक्खी का मोम', 'মৌমাছির মোম', 600.0, 'kg'),
    ('propolis', 'प्रोपोलिस', 'প্রোপোলিস', 1800.0, 'kg'),
    ('royal jelly', 'रॉयल जैली', 'রয়্যাল জেলি', 8000.0, 'kg'),
    ('bee venom', 'मधुमक्खी का विष', 'মৌমাছির বিষ', 50000.0, 'kg'),
    ('mulberry silkworm cocoon', 'शहतूत रेशमकीट कोकून', 'তুঁত রেশম পোকার গুটি', 650.0, 'kg'),
    ('eri silkworm cocoon', 'एरी रेशमकीट कोकून', 'এরিয়া রেশম পোকার গুটি', 750.0, 'kg'),
    ('tasar silkworm cocoon', 'टसर रेशमकीट कोकून', 'তসর রেশম পোকার গুটি', 850.0, 'kg'),
    ('muga silkworm cocoon', 'मूंगा रेशमकीट कोकून', 'মুগা রেশম পোকার গুটি', 1200.0, 'kg'),
    ('raw silk yarn', 'कच्चा रेशमी धागा', 'কাঁচা রেশমি সুতা', 4500.0, 'kg'),
    ('jaggery', 'गुड़', 'গুড়', 50.0, 'kg'),
    ('gur', 'गुड़', 'গুড়', 50.0, 'kg'),
    ('jaggery powder', 'गुड़ पाउडर', 'গুড় গুঁড়ো', 65.0, 'kg'),
    ('khandsari sugar', 'खांडसारी चीनी', 'খান্ডসারি চিনি', 60.0, 'kg'),
    ('white sugar', 'सफेद चीनी', 'সাদা চিনি', 45.0, 'kg'),
    ('stone-ground whole wheat flour', 'पत्थर चक्की गेहूं आटा', 'পাথরে ভাঙা গমের আটা', 55.0, 'kg'),
    ('chakki atta', 'चक्की आटा', 'চাক্কি আটা', 55.0, 'kg'),
    ('multi-grain flour', 'मल्टीग्रेन आटा', 'মাল্টিগ্রেন আটা', 75.0, 'kg'),
    ('rice flour', 'चावल का आटा', 'চালের গুঁড়ো', 65.0, 'kg'),
    ('maida', 'मैदा', 'ময়দা', 45.0, 'kg'),
    ('suji', 'सूजी', 'সুজি', 50.0, 'kg'),
    ('besan', 'बेसन', 'বেসন', 110.0, 'kg'),
    ('cold-pressed mustard oil', 'कोल्ड-प्रेस्ड सरसों तेल', 'কোল্ড-প্রেসড সরষের তেল', 220.0, 'litre'),
    ('kachi ghani sarson tel', 'कच्ची घानी सरसों तेल', 'কাচ্চি ঘানি সরষের তেল', 225.0, 'litre'),
    ('cold-pressed coconut oil', 'कोल्ड-प्रेस्ड नारियल तेल', 'কোল্ড-প্রেসড নারকেল তেল', 350.0, 'litre'),
    ('virgin coconut oil', 'वर्जिन नारियल तेल', 'ভার্জিন নারকেল তেল', 420.0, 'litre'),
    ('cold-pressed groundnut oil', 'कोल्ड-प्रेस्ड मूंगफली तेल', 'কোল্ড-প্রেসড বাদাম তেল', 220.0, 'litre'),
    ('sesame oil', 'तिल का तेल', 'তিলের তেল', 320.0, 'litre'),
    ('sunflower oil', 'सूरजमुखी तेल', 'সূর্যমুখী তেল', 150.0, 'litre'),
    ('soy oil', 'सोया तेल', 'সয়া তেল', 145.0, 'litre'),
    ('linseed oil', 'अलसी का तेल', 'তিসির তেল', 280.0, 'litre'),
    ('homemade cow ghee', 'घर का बना गाय का घी', 'ঘরে তৈরি গরুর ঘি', 650.0, 'kg'),
    ('desi ghee', 'देसी घी', 'দেশি ঘি', 620.0, 'kg'),
    ('buffalo ghee', 'भैंस का घी', 'মহিষের ঘি', 580.0, 'kg'),
    ('fresh paneer', 'ताजा पनीर', 'টাটকা পনির', 380.0, 'kg'),
    ('butter', 'मक्खन', 'মাখন', 450.0, 'kg'),
    ('white butter', 'सफेद मक्खन', 'সাদা মাখন', 460.0, 'kg'),
    ('curd', 'दही', 'দই', 70.0, 'kg'),
    ('dahi', 'दही', 'দই', 70.0, 'kg'),
    ('buttermilk', 'छाछ', 'ঘোল', 40.0, 'litre'),
    ('chaas', 'छाछ', 'ঘোল', 40.0, 'litre'),
    ('khoa', 'खोया', 'খোয়া', 320.0, 'kg'),
    ('mawa', 'मावा', 'মাওয়া', 320.0, 'kg'),
    ('cheese', 'चीज़', 'চিজ', 480.0, 'kg'),
    ('goat milk soap', 'बकरी के दूध का साबुन', 'ছাগলের দুধের সাবান', 120.0, 'piece'),
    ('fruit jam', 'फलों का जैम', 'ফলের জ্যাম', 280.0, 'kg'),
    ('mixed fruit jelly', 'मिश्रित फलों की जैली', 'মিশ্র ফলের জেলি', 260.0, 'kg'),
    ('apple juice', 'सेब का रस', 'আপেলের রস', 130.0, 'litre'),
    ('mango pulp', 'आम का गूदा', 'আমের শাঁস', 150.0, 'kg'),
    ('tomato puree', 'टमाटर प्यूरी', 'টমেটো পিউরি', 120.0, 'kg'),
    ('tomato powder', 'टमाटर पाउडर', 'টমেটো গুঁড়ো', 350.0, 'kg'),
    ('potato chips', 'आलू चिप्स', 'আলুর চিপস', 250.0, 'kg'),
    ('sun-dried papad', 'धूप में सुखाया पापड़', 'রোদে শুকানো পাঁপড়', 220.0, 'kg'),
    ('mango pickle', 'आम का अचार', 'আমের আচার', 250.0, 'kg'),
    ('lime pickle', 'नींबू का अचार', 'লেবুর আচার', 230.0, 'kg'),
    ('chilli pickle', 'मिर्च का अचार', 'লঙ্কার আচার', 260.0, 'kg'),
    ('garlic paste', 'लहसुन का पेस्ट', 'রসুন বাটা', 180.0, 'kg'),
    ('ginger paste', 'अदरक का पेस्ट', 'আদা বাটা', 170.0, 'kg'),
    ('cocoa butter', 'कोको बटर', 'কোকো বাটার', 900.0, 'kg'),
    ('chocolate paste', 'चॉकलेट पेस्ट', 'চকলেট পেস্ট', 550.0, 'kg'),
]

# Build DB with auto IDs
products_db: List[ProductPrice] = [
    ProductPrice(id=i + 1, product_name=n, hindi_name=h, bengali_name=b,
                 market_price_per_kg=p, unit=u)
    for i, (n, h, b, p, u) in enumerate(RAW_PRODUCTS)
]

# Title Case product names: raw honey -> Raw Honey, duck egg -> Duck Egg
for _p in products_db:
    _p.product_name = _p.product_name.title()


# ---------------- Plural-tolerant search ----------------
# potato / potatos / potatoes -> same, onion / onions -> same, etc.
# Applied to ALL products.

def normalize_word(w: str) -> str:
    w = w.lower()
    if w == "leaves":
        return "leaf"
    if w == "leaf":
        return "leaf"
    # step 1: plural stripping
    if w.endswith("ies") and len(w) > 3:
        # chillies -> chilli, strawberries -> strawberri
        w = w[:-3] + "i"
    elif w.endswith("oes") and len(w) > 3:
        # potatoes -> potato, tomatoes -> tomato, mangoes -> mango
        w = w[:-2]
    elif w.endswith("ches") or w.endswith("shes") or w.endswith("sses") or w.endswith("xes") or w.endswith("zes"):
        # peaches -> peach, boxes -> box
        if len(w) > 5:
            w = w[:-2]
    elif w.endswith("s") and not w.endswith("ss") and len(w) > 2:
        # onions -> onion, potatos (user typo) -> potato, eggs -> egg, honeys -> honey
        w = w[:-1]
    # step 2: y -> i so chilly/chilli, strawberry/strawberri, honey/honeys stay same
    if w.endswith("y") and len(w) > 2:
        w = w[:-1] + "i"
    return w


def normalize_name(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    words = s.split()
    words = [normalize_word(w) for w in words]
    return " ".join(words)


# Precompute normalized index: normalized_name -> product
_normalized_index = {normalize_name(p.product_name): p for p in products_db}
_normalized_list = [(p, normalize_name(p.product_name)) for p in products_db]


def find_all_by_product(name: str) -> List[ProductPrice]:
    key = normalize_name(name)
    # 1. exact normalized match (plural-tolerant) -> single-item list
    # e.g. potato -> [potato], raw honey -> [raw honey]
    if key in _normalized_index:
        return [_normalized_index[key]]
    query_words = key.split()
    # 2. whole-word fallback: all query words appear as whole words in product
    # e.g. honey -> [raw honey, mustard honey, ...], egg -> [poultry egg, duck egg]
    # milk -> [cow milk, ...] (not milky mushroom)
    whole = []
    for p, norm in _normalized_list:
        prod_words = norm.split()
        if all(qw in prod_words for qw in query_words):
            whole.append(p)
    if whole:
        # fewest extra words first, then earliest curated default (raw honey first)
        whole.sort(key=lambda p: (len(normalize_name(p.product_name).split()) - len(query_words), p.id))
        return whole
    # 3. substring fallback (last resort) -> all substring matches
    candidates = [
        p for p, norm in _normalized_list
        if key in norm or norm in key
    ]
    return candidates


# ---------------- Routes (search only) ----------------

@app.get("/products/", response_model=List[ProductPrice])
def search_product(name: str = Query(..., description="Product name e.g. rice, wheat, onion. Plural-tolerant: potato, potatos, potatoes all work. Generic: egg -> poultry egg + duck egg, honey -> all honeys.")):
    """
    User puts product name, market price(s) come.
    Example: GET /products/?name=potato  -> [potato]
             GET /products/?name=egg     -> [poultry egg, duck egg]
             GET /products/?name=honey   -> [raw honey, mustard honey, ...]
    """
    results = find_all_by_product(name)
    if not results:
        raise HTTPException(status_code=404, detail=f"No product found with name '{name}'")
    # Add Rs formatted price, e.g. "Rs 28 per kg"
    for r in results:
        r.market_price = f"Rs {r.market_price_per_kg:g} per {r.unit}"
    return results