import enum


class UserRole(str, enum.Enum):
    INSPECTOR = "INSPECTOR"
    SUPERVISOR = "SUPERVISOR"
    ADMIN = "ADMIN"


class ProductCategory(str, enum.Enum):
    FOOD_BEVERAGE = "FOOD_BEVERAGE"
    COSMETIC_PERSONAL_CARE = "COSMETIC_PERSONAL_CARE"
    ELECTRONICS = "ELECTRONICS"
    HOUSEHOLD = "HOUSEHOLD"
    GENERAL = "GENERAL"


class InspectionStatus(str, enum.Enum):
    CREATED = "CREATED"
    PROCESSING = "PROCESSING"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    COMPLETED = "COMPLETED"


class ComplianceResult(str, enum.Enum):
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    PENDING = "PENDING"


class CheckResult(str, enum.Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    REVIEW = "REVIEW"


class ImageType(str, enum.Enum):
    FRONT = "FRONT"
    BACK = "BACK"
    SIDE = "SIDE"
    TOP = "TOP"
    BOTTOM = "BOTTOM"
    LABEL = "LABEL"
    OTHER = "OTHER"


class ViolationSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ViolationStatus(str, enum.Enum):
    OPEN = "OPEN"
    REVIEWED = "REVIEWED"
    RESOLVED = "RESOLVED"


class EvidenceType(str, enum.Enum):
    BOUNDING_BOX = "BOUNDING_BOX"
    CROPPED_IMAGE = "CROPPED_IMAGE"
    OCR_SNIPPET = "OCR_SNIPPET"
    MANUAL_ANNOTATION = "MANUAL_ANNOTATION"


class ReportType(str, enum.Enum):
    PDF = "PDF"
    JSON = "JSON"
    INSPECTION_MEMO = "INSPECTION_MEMO"
    NOTICE_SEC36 = "NOTICE_SEC36"


class RuleType(str, enum.Enum):
    REQUIRED_FIELD = "REQUIRED_FIELD"
    FORMAT_CHECK = "FORMAT_CHECK"
    NUMERAL_HEIGHT = "NUMERAL_HEIGHT"
    UNIT_CHECK = "UNIT_CHECK"
    EXPIRY_DATE_CHECK = "EXPIRY_DATE_CHECK"
    CUSTOM_LOGIC = "CUSTOM_LOGIC"

