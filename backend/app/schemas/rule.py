import uuid
from datetime import datetime
from typing import Any, Dict, List
from pydantic import BaseModel, ConfigDict
from app.core.enums import RuleType


class LegalRuleBase(BaseModel):
    rule_code: str
    title: str
    description: str
    field_name: str | None = None
    rule_type: RuleType = RuleType.REQUIRED_FIELD
    parameters: Dict[str, Any] | None = None
    version: str = "2011.1"
    source_reference: str
    penalty_clause: str | None = None
    category_applicability: List[str] | None = None
    is_active: bool = True


class LegalRuleCreate(LegalRuleBase):
    pass


class LegalRuleResponse(LegalRuleBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

