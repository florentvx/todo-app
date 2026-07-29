from __future__ import annotations
import uuid
from dataclasses import dataclass, field

CALENDAR_COLORS = {
    "default": "#555555",
    "red": "#e74c3c",
    "blue": "#3498db",
    "green": "#2ecc71",
    "yellow": "#f1c40f",
    "orange": "#e67e22",
    "purple": "#9b59b6",
}


@dataclass
class CalendarEntry:
    date: str
    title: str = ""
    notes: str = ""
    color: str = "default"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict:
        return {"id": self.id, "date": self.date, "title": self.title, "notes": self.notes, "color": self.color}

    @classmethod
    def from_dict(cls, data: dict) -> CalendarEntry:
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            date=data["date"],
            title=data.get("title", ""),
            notes=data.get("notes", ""),
            color=data.get("color", "default"),
        )
