from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.core.enums import CheckResult


@dataclass
class DigitalListingData:
    title: Optional[str]
    description: Optional[str]
    price: Optional[float]
    country_of_origin: Optional[str]
    net_quantity: Optional[str]
    manufacturer_name: Optional[str]
    listing_url: Optional[str]
    captured_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "price": self.price,
            "country_of_origin": self.country_of_origin,
            "net_quantity": self.net_quantity,
            "manufacturer_name": self.manufacturer_name,
            "listing_url": self.listing_url,
            "captured_at": self.captured_at.isoformat() if self.captured_at else None,
        }


@dataclass
class ListingCrossCheckItem:
    field: str
    listing_value: Optional[str]
    package_value: Optional[str]
    status: str  # "MATCH", "DISCREPANCY", "PARTIAL", "NOT_APPLICABLE"
    finding: str
    result: CheckResult


@dataclass
class DigitalListingCrossCheckReport:
    has_contradictions: bool
    items: List[ListingCrossCheckItem]
    summary_verdict: CheckResult
    summary_reason: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "has_contradictions": self.has_contradictions,
            "summary_verdict": self.summary_verdict.value,
            "summary_reason": self.summary_reason,
            "items": [
                {
                    "field": it.field,
                    "listing_value": it.listing_value,
                    "package_value": it.package_value,
                    "status": it.status,
                    "finding": it.finding,
                    "result": it.result.value,
                }
                for it in self.items
            ],
        }


def cross_check_digital_listing(
    listing: DigitalListingData,
    declaration: Optional[Any],
) -> DigitalListingCrossCheckReport:
    """
    Cross-checks controlled digital product marketplace listing data against
    physical package photograph declarations under Rule 6(10) of LMPC Rules.
    Strict Guardrail: Contradictory values produce REVIEW with neutral terminology.
    """
    items: List[ListingCrossCheckItem] = []
    has_discrepancy = False

    if not declaration:
        return DigitalListingCrossCheckReport(
            has_contradictions=False,
            items=[],
            summary_verdict=CheckResult.REVIEW,
            summary_reason="Physical package declaration data unavailable for cross-referencing.",
        )

    # 1. Country of Origin Cross-Check
    listing_origin = (listing.country_of_origin or "").strip().lower()
    pkg_origin = (declaration.country_of_origin or "").strip().lower()
    if listing_origin and pkg_origin:
        if listing_origin == pkg_origin:
            items.append(
                ListingCrossCheckItem(
                    field="country_of_origin",
                    listing_value=listing.country_of_origin,
                    package_value=declaration.country_of_origin,
                    status="MATCH",
                    finding=f"Country of origin matches between digital listing and physical package ('{declaration.country_of_origin}').",
                    result=CheckResult.PASS,
                )
            )
        else:
            has_discrepancy = True
            items.append(
                ListingCrossCheckItem(
                    field="country_of_origin",
                    listing_value=listing.country_of_origin,
                    package_value=declaration.country_of_origin,
                    status="DISCREPANCY",
                    finding=f"Contradictory declaration detected: Digital marketplace listing states '{listing.country_of_origin}' but physical package label declares '{declaration.country_of_origin}'.",
                    result=CheckResult.REVIEW,
                )
            )

    # 2. Net Quantity Cross-Check
    listing_qty = (listing.net_quantity or "").strip().lower()
    pkg_qty = (declaration.net_quantity or "").strip().lower()
    if listing_qty and pkg_qty:
        if listing_qty == pkg_qty:
            items.append(
                ListingCrossCheckItem(
                    field="net_quantity",
                    listing_value=listing.net_quantity,
                    package_value=declaration.net_quantity,
                    status="MATCH",
                    finding=f"Declared net quantity matches between listing and physical package ('{declaration.net_quantity}').",
                    result=CheckResult.PASS,
                )
            )
        else:
            has_discrepancy = True
            items.append(
                ListingCrossCheckItem(
                    field="net_quantity",
                    listing_value=listing.net_quantity,
                    package_value=declaration.net_quantity,
                    status="DISCREPANCY",
                    finding=f"Quantity discrepancy: Digital listing shows '{listing.net_quantity}' while physical package displays '{declaration.net_quantity}'.",
                    result=CheckResult.REVIEW,
                )
            )

    # 3. Price / MRP Cross-Check
    if listing.price is not None and declaration.mrp:
        from app.services.barcode_service import extract_numeric_mrp
        pkg_mrp_num = extract_numeric_mrp(declaration.mrp)
        if pkg_mrp_num is not None:
            diff = abs(listing.price - pkg_mrp_num)
            if diff <= 0.05:
                items.append(
                    ListingCrossCheckItem(
                        field="mrp",
                        listing_value=f"₹{listing.price:.2f}",
                        package_value=declaration.mrp,
                        status="MATCH",
                        finding=f"Digital listing price (₹{listing.price:.2f}) matches physical package MRP (₹{pkg_mrp_num:.2f}).",
                        result=CheckResult.PASS,
                    )
                )
            else:
                has_discrepancy = True
                items.append(
                    ListingCrossCheckItem(
                        field="mrp",
                        listing_value=f"₹{listing.price:.2f}",
                        package_value=declaration.mrp,
                        status="DISCREPANCY",
                        finding=f"Price discrepancy detected: Digital listing offers product at ₹{listing.price:.2f} while physical package declares MRP ₹{pkg_mrp_num:.2f}.",
                        result=CheckResult.REVIEW,
                    )
                )

    if has_discrepancy:
        summary_verdict = CheckResult.REVIEW
        summary_reason = "Discrepancy detected between digital product listing and physical package declarations; inspector review required under Rule 6(10)."
    else:
        summary_verdict = CheckResult.PASS
        summary_reason = "Digital marketplace declarations are consistent with physical package evidence."

    return DigitalListingCrossCheckReport(
        has_contradictions=has_discrepancy,
        items=items,
        summary_verdict=summary_verdict,
        summary_reason=summary_reason,
    )

