import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image

try:
    import zxingcpp
    ZXING_AVAILABLE = True
except ImportError:
    ZXING_AVAILABLE = False


@dataclass
class BarcodeDetectionResult:
    value: str
    format: str
    bounding_box: Optional[Dict[str, int]]  # {"x": ..., "y": ..., "width": ..., "height": ...}
    source_image_id: Optional[uuid.UUID] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "format": self.format,
            "bounding_box": self.bounding_box,
            "source_image_id": str(self.source_image_id) if self.source_image_id else None,
        }


# Controlled Demo Master Catalog
# Sourced strictly for demonstration and testing of Legal Metrology compliance checks.
# EXPLICIT NOTICE: This is controlled demo data and is NOT an official government or ministry database.
CONTROLLED_DEMO_CATALOG: Dict[str, Dict[str, Any]] = {
    "8901030889211": {
        "barcode": "8901030889211",
        "commodity_name": "Tata Sampann 100% Unpolished Toor Dal",
        "brand_name": "Tata Sampann",
        "manufacturer_name": "Tata Consumer Products Ltd",
        "category": "FOOD_AND_BEVERAGES",
        "standard_mrp": 175.00,
        "standard_net_quantity": "1 kg",
        "is_demo_record": True,
        "description": "Standard 1kg Toor Dal pouch (Controlled Demo Catalog Record — Not an official government database)",
    },
    "8901499009852": {
        "barcode": "8901499009852",
        "commodity_name": "Amul Pure Ghee Pouch",
        "brand_name": "Amul",
        "manufacturer_name": "Gujarat Co-operative Milk Marketing Federation Ltd",
        "category": "FOOD_AND_BEVERAGES",
        "standard_mrp": 560.00,
        "standard_net_quantity": "1 L",
        "is_demo_record": True,
        "description": "Pure Ghee 1L pouch (Controlled Demo Catalog Record — Not an official government database)",
    },
    "8901725181220": {
        "barcode": "8901725181220",
        "commodity_name": "Aashirvaad Superior MP Shudh Chakki Atta",
        "brand_name": "Aashirvaad",
        "manufacturer_name": "ITC Limited",
        "category": "FOOD_AND_BEVERAGES",
        "standard_mrp": 240.00,
        "standard_net_quantity": "5 kg",
        "is_demo_record": True,
        "description": "Chakki Atta 5kg bag (Controlled Demo Catalog Record — Not an official government database)",
    },
    "8901058852310": {
        "barcode": "8901058852310",
        "commodity_name": "Parle-G Gold Biscuits",
        "brand_name": "Parle",
        "manufacturer_name": "Parle Products Pvt Ltd",
        "category": "FOOD_AND_BEVERAGES",
        "standard_mrp": 120.00,
        "standard_net_quantity": "1 kg",
        "is_demo_record": True,
        "description": "Gold Biscuits 1kg pack (Controlled Demo Catalog Record — Not an official government database)",
    },
    "8906010500123": {
        "barcode": "8906010500123",
        "commodity_name": "Fortune Sunlite Refined Sunflower Oil",
        "brand_name": "Fortune",
        "manufacturer_name": "Adani Wilmar Limited",
        "category": "FOOD_AND_BEVERAGES",
        "standard_mrp": 145.00,
        "standard_net_quantity": "1 L",
        "is_demo_record": True,
        "description": "Refined Sunflower Oil 1L (Controlled Demo Catalog Record — Not an official government database)",
    },
}


def decode_barcodes_from_image(
    image_path: Path,
    image_id: Optional[uuid.UUID] = None,
) -> List[BarcodeDetectionResult]:
    """
    Decodes standard 1D/2D barcodes (EAN-13, EAN-8, UPC-A, QR Code, Code 128)
    from a package photograph using local ZXing-C++ engine.
    """
    if not image_path.exists() or not ZXING_AVAILABLE:
        return []

    try:
        with Image.open(image_path) as img:
            # ZXing works directly with PIL Images
            results = zxingcpp.read_barcodes(img)
            detections: List[BarcodeDetectionResult] = []

            for r in results:
                val = r.text.strip()
                if not val:
                    continue

                fmt_str = str(r.format).split(".")[-1].upper()

                # Calculate bounding box from corner polygon
                bbox = None
                if hasattr(r, "position") and r.position:
                    pos = r.position
                    xs = [pos.top_left.x, pos.top_right.x, pos.bottom_right.x, pos.bottom_left.x]
                    ys = [pos.top_left.y, pos.top_right.y, pos.bottom_right.y, pos.bottom_left.y]
                    min_x, max_x = max(0, min(xs)), max(xs)
                    min_y, max_y = max(0, min(ys)), max(ys)
                    bbox = {
                        "x": int(min_x),
                        "y": int(min_y),
                        "width": int(max(1, max_x - min_x)),
                        "height": int(max(1, max_y - min_y)),
                    }

                detections.append(
                    BarcodeDetectionResult(
                        value=val,
                        format=fmt_str,
                        bounding_box=bbox,
                        source_image_id=image_id,
                    )
                )

            return detections

    except Exception:
        return []


def lookup_master_catalog(barcode: str) -> Optional[Dict[str, Any]]:
    """
    Looks up a product by barcode in the controlled master catalog.
    """
    cleaned_barcode = barcode.strip().replace("-", "").replace(" ", "")
    return CONTROLLED_DEMO_CATALOG.get(cleaned_barcode)


def extract_numeric_mrp(mrp_str: Optional[str]) -> Optional[float]:
    """
    Extracts the first valid numeric floating point value from an MRP string.
    Example: 'MRP Rs. 420.00 (incl. of all taxes)' -> 420.00
    """
    if not mrp_str:
        return None
    
    # Matches patterns like 420, 420.00, 420.50
    matches = re.findall(r"(?:rs\.?|₹|mrp)?\s*([0-9]+(?:\.[0-9]{1,2})?)", mrp_str, re.IGNORECASE)
    if matches:
        try:
            return float(matches[0])
        except ValueError:
            return None
    return None


def verify_mrp_against_catalog(
    observed_mrp_str: Optional[str],
    catalog_product: Optional[Dict[str, Any]],
) -> Tuple[str, str, Optional[float], Optional[float]]:
    """
    Compares observed printed label MRP against the registered demo catalog MRP.
    
    Returns:
    (comparison_status, reason_description, observed_numeric_mrp, catalog_mrp)
    
    Status values:
    - MATCH: Observed MRP equals catalog MRP.
    - MISMATCH: Observed MRP differs from catalog MRP.
    - NO_OBSERVED_MRP: Observed MRP was not found/extracted on package.
    - NO_CATALOG_MATCH: Barcode not registered in controlled master catalog.
    """
    if not catalog_product:
        return ("NO_CATALOG_MATCH", "Barcode not registered in controlled master catalog.", None, None)

    catalog_mrp = float(catalog_product.get("standard_mrp", 0.0))
    observed_mrp_num = extract_numeric_mrp(observed_mrp_str)

    if observed_mrp_num is None:
        return (
            "NO_OBSERVED_MRP",
            f"Package barcode matched '{catalog_product.get('commodity_name')}' (Controlled Catalog Reference: ₹{catalog_mrp:.2f}), but printed label MRP was not detected on package.",
            None,
            catalog_mrp,
        )

    # Check for discrepancy with tolerance of 0.05 for float precision
    diff = abs(observed_mrp_num - catalog_mrp)
    if diff <= 0.05:
        return (
            "MATCH",
            f"Observed package MRP (₹{observed_mrp_num:.2f}) matches controlled master catalog reference (₹{catalog_mrp:.2f}).",
            observed_mrp_num,
            catalog_mrp,
        )
    else:
        return (
            "MISMATCH",
            f"MRP discrepancy detected against reference data: Observed package MRP (₹{observed_mrp_num:.2f}) differs from controlled master catalog reference (₹{catalog_mrp:.2f}). Inspector physical verification required under Rule 18(2).",
            observed_mrp_num,
            catalog_mrp,
        )
