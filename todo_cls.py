import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime

VALID_PRIORITIES = {"high", "normal", "low"}
VALID_VERSIONS = {1, 2}
LEGACY_DELIVERY_DATE = "2100-01-01"


@dataclass
class Todo:
    text: str
    priority: str = "normal"
    comment: str = ""
    done: bool = False
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    version: int = 1
    delivery_date: str | None = None

    def __post_init__(self):
        self.text = self.text.strip()
        self.comment = self.comment.strip()
        if self.version not in VALID_VERSIONS:
            raise ValueError(f"version must be one of {VALID_VERSIONS}, got {self.version}")
        if self.priority not in VALID_PRIORITIES:
            raise ValueError(f"priority must be one of {VALID_PRIORITIES}, got '{self.priority}'")
        uuid.UUID(self.id)
        if self.version == 1 and self.delivery_date is not None:
            raise ValueError("version 1 todos must not have a delivery_date")
        if self.version == 2 and self.delivery_date is None:
            raise ValueError("version 2 todos must have a delivery_date")

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Todo":
        filtered = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        if "version" not in filtered:
            raise NotImplementedError()
            # if "delivery_date" in filtered and filtered["delivery_date"] != LEGACY_DELIVERY_DATE:
            #     filtered["version"] = 2
            # else:
            #     filtered["version"] = 1
            #     filtered.pop("delivery_date", None)
        return cls(**filtered)

    def get_delivery_date(self):
        return self.delivery_date if self.delivery_date is not None else LEGACY_DELIVERY_DATE