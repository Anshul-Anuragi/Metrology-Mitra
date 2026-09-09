"""
Phase 4.5 P0 Hardening — Deterministic Controlled Semantic Vocabulary
=====================================================================
Engineering interpretation layer defining aliases, keyword patterns, and
OCR-tolerant matching for statutory declaration fields under the Legal
Metrology (Packaged Commodities) Rules, 2011.

ARCHITECTURAL NOTICE:
This vocabulary is an engineering interpretation layer to associate optical
tokens with candidate declaration fields. It does NOT constitute a statutory
determination or certification by itself. The deterministic legal rule engine
remains the sole statutory authority.
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Pattern


@dataclass
class VocabularyField:
    canonical_name: str
    statutory_rule: str
    aliases_en: List[str]
    aliases_hi: List[str]
    pattern: Pattern
    is_numeric: bool = False
    expected_units: List[str] = field(default_factory=list)


# 1. Controlled Keyword Definitions
VOCABULARY_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "MRP": {
        "statutory_rule": "Rule 6(1)(da) / Rule 6(1)(e)",
        "aliases_en": [
            "mrp", "m.r.p.", "m r p", "maximum retail price", "max retail price",
            "max. retail price", "retail price", "max retail",
        ],
        "aliases_hi": [
            "अधिकतम खुदरा मूल्य", "अ.खु.मू.", "अ०खु०मू०", "खुदरा मूल्य", "एमआरपी", "एम.आर.पी.",
        ],
        "pattern": re.compile(
            r"(?i)\b(?:m\.?r\.?p\.?|m\s*r\s*p|maximum\s+retail\s+price|max\.?\s*retail\s*price|retail\s+price|"
            r"अधिकतम\s*खुदरा\s*मूल्य|अ\.?खु\.?मू\.?|अ०खु०मू०|एम\.?आर\.?पी\.?)\b"
        ),
        "is_numeric": True,
        "expected_units": ["₹", "rs", "inr", "रु", "रुपये"],
    },
    "NET_QUANTITY": {
        "statutory_rule": "Rule 6(1)(c), Schedule II",
        "aliases_en": [
            "net quantity", "net qty", "net wt", "net weight", "net content",
            "net contents", "net volume", "net mass", "contents", "quantity",
        ],
        "aliases_hi": [
            "शुद्ध मात्रा", "नेट मात्रा", "मात्रा", "शुद्ध वजन", "नेट वजन", "वजन",
        ],
        "pattern": re.compile(
            r"(?i)\b(?:net\s*(?:quantity|qty|wt|weight|content|contents|volume|mass)?|"
            r"शुद्ध\s*(?:मात्रा|वजन)|नेट\s*(?:मात्रा|वजन)|मात्रा)\b"
        ),
        "is_numeric": True,
        "expected_units": ["g", "kg", "mg", "ml", "l", "ltr", "gm", "gms", "kgs", "n", "u", "cm", "m"],
    },
    "UNIT_SALE_PRICE": {
        "statutory_rule": "Rule 6(1)(f)",
        "aliases_en": [
            "unit sale price", "usp", "u.s.p.", "unit price",
        ],
        "aliases_hi": [
            "प्रति इकाई विक्रय मूल्य", "इकाई मूल्य",
        ],
        "pattern": re.compile(
            r"(?i)\b(?:unit\s*sale\s*price|u\.?s\.?p\.?|unit\s*price|प्रति\s*इकाई\s*विक्रय\s*मूल्य)\b"
        ),
        "is_numeric": True,
        "expected_units": ["/g", "/kg", "/ml", "/l", "/n", "/u", "/piece"],
    },
    "MANUFACTURER": {
        "statutory_rule": "Rule 6(1)(b)",
        "aliases_en": [
            "manufactured by", "manufacturer", "mfd by", "mfg by", "produced by",
            "made by", "processed by",
        ],
        "aliases_hi": [
            "निर्माता", "निर्माण", "उत्पादक", "तैयारकर्ता",
        ],
        "pattern": re.compile(
            r"(?i)\b(?:manufactured\s+by|manufacturer|mfd\.?\s*by|mfg\.?\s*by|produced\s+by|made\s+by|"
            r"निर्माता|द्वारा\s*निर्मित|उत्पादक)\b"
        ),
        "is_numeric": False,
    },
    "PACKER": {
        "statutory_rule": "Rule 6(1)(b)",
        "aliases_en": [
            "packed by", "packer", "pkd by", "packaged by", "pre-packed by",
        ],
        "aliases_hi": [
            "पैकर", "पैकिंग\s*कर्ता", "द्वारा\s*पैक",
        ],
        "pattern": re.compile(
            r"(?i)\b(?:packed\s+by|packer|pkd\.?\s*by|packaged\s+by|pre-packed\s+by|"
            r"पैकर|पैकिंग\s*कर्ता|द्वारा\s*पैक)\b"
        ),
        "is_numeric": False,
    },
    "IMPORTER": {
        "statutory_rule": "Rule 6(1)(b) / Rule 6(10)",
        "aliases_en": [
            "imported by", "importer", "import by",
        ],
        "aliases_hi": [
            "आयातकर्ता", "द्वारा\s*आयातित",
        ],
        "pattern": re.compile(
            r"(?i)\b(?:imported\s+by|importer|import\s+by|आयातकर्ता|द्वारा\s*आयातित)\b"
        ),
        "is_numeric": False,
    },
    "COMMODITY": {
        "statutory_rule": "Rule 6(1)(a)",
        "aliases_en": [
            "commodity", "product", "item", "product name", "generic name",
        ],
        "aliases_hi": [
            "वस्तु", "उत्पाद", "सामग्री", "उत्पाद\s*का\s*नाम",
        ],
        "pattern": re.compile(
            r"(?i)\b(?:commodity|product(?:\s*name)?|item(?:\s*name)?|generic\s*name|उत्पाद|वस्तु|सामग्री)\b"
        ),
        "is_numeric": False,
    },
    "CONSUMER_CARE": {
        "statutory_rule": "Rule 6(1)(e) / Rule 6(1)(h)",
        "aliases_en": [
            "customer care", "consumer care", "customer service", "consumer cell",
            "grievance cell", "helpline", "toll free", "call us", "contact us",
            "feedback",
        ],
        "aliases_hi": [
            "उपभोक्ता देखभाल", "ग्राहक सेवा", "शिकायत प्रकोष्ठ", "टोल फ्री",
        ],
        "pattern": re.compile(
            r"(?i)\b(?:consumer\s*care|customer\s*care|customer\s*service|consumer\s*cell|"
            r"grievance\s*cell|helpline|toll\s*free|call\s*us|contact\s*us|feedback|"
            r"उपभोक्ता\s*देखभाल|ग्राहक\s*सेवा)\b"
        ),
        "is_numeric": False,
    },
    "MANUFACTURING_DATE": {
        "statutory_rule": "Rule 6(1)(d)",
        "aliases_en": [
            "mfg date", "mfd date", "date of mfg", "date of manufacture", "mfd", "mfg",
            "manufactured on",
        ],
        "aliases_hi": [
            "निर्माण तिथि", "उत्पादन तिथि",
        ],
        "pattern": re.compile(
            r"(?i)\b(?:mfg\.?\s*date|mfd\.?\s*date|date\s*of\s*mfg|date\s*of\s*manufacture|"
            r"mfd|mfg|manufactured\s*on|निर्माण\s*तिथि|उत्पादन\s*तिथि)\b"
        ),
        "is_numeric": False,
    },
    "PACKING_DATE": {
        "statutory_rule": "Rule 6(1)(d)",
        "aliases_en": [
            "pkd date", "date of packing", "pkd", "packed on", "pkg date",
        ],
        "aliases_hi": [
            "पैकिंग तिथि", "पैक तिथि",
        ],
        "pattern": re.compile(
            r"(?i)\b(?:pkd\.?\s*date|date\s*of\s*packing|pkd|packed\s*on|pkg\.?\s*date|पैकिंग\s*तिथि|पैक\s*तिथि)\b"
        ),
        "is_numeric": False,
    },
    "EXPIRY_DATE": {
        "statutory_rule": "Rule 6(1)(d)",
        "aliases_en": [
            "exp date", "expiry date", "expiry", "exp", "use by",
        ],
        "aliases_hi": [
            "अवसान तिथि", "समाप्ति तिथि", "उपयोग की अंतिम तिथि",
        ],
        "pattern": re.compile(
            r"(?i)\b(?:exp\.?\s*date|expiry(?:\s*date)?|use\s*by|exp|अवसान\s*तिथि|समाप्ति\s*तिथि)\b"
        ),
        "is_numeric": False,
    },
    "BEST_BEFORE": {
        "statutory_rule": "Rule 6(1)(d)",
        "aliases_en": [
            "best before", "best by",
        ],
        "aliases_hi": [
            "से पहले सबसे अच्छा",
        ],
        "pattern": re.compile(
            r"(?i)\b(?:best\s*before|best\s*by|से\s*पहले\s*सबसे\s*अच्छा)\b"
        ),
        "is_numeric": False,
    },
    "COUNTRY_OF_ORIGIN": {
        "statutory_rule": "Rule 6(10) / Rule 6(1)(j)",
        "aliases_en": [
            "country of origin", "made in", "origin", "country of manufacture",
        ],
        "aliases_hi": [
            "मूल देश", "उत्पत्ति का देश",
        ],
        "pattern": re.compile(
            r"(?i)\b(?:country\s*of\s*origin|made\s*in|country\s*of\s*manufacture|मूल\s*देश)\b"
        ),
        "is_numeric": False,
    },
}
