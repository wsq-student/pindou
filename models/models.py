from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


@dataclass
class InventoryItem:
    code: str
    current_stock: int
    warning_threshold: int = 10
    update_time: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "InventoryItem":
        return cls(
            code=str(data.get("code", "")).strip().upper(),
            current_stock=int(data.get("current_stock", 0)),
            warning_threshold=int(data.get("warning_threshold", 10)),
            update_time=str(data.get("update_time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))),
        )

    @property
    def is_low_stock(self) -> bool:
        return self.current_stock <= self.warning_threshold


@dataclass
class ColorMapping:
    code: str
    color_hex: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ColorMapping":
        return cls(
            code=str(data.get("code", "")).strip().upper(),
            color_hex=str(data.get("color_hex", "")).strip(),
        )


@dataclass
class PatternRecord:
    id: str
    pattern_name: str
    image_path: str
    create_time: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "PatternRecord":
        return cls(
            id=str(data.get("id", "")),
            pattern_name=str(data.get("pattern_name", "")),
            image_path=str(data.get("image_path", "")),
            create_time=str(data.get("create_time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))),
        )


@dataclass
class PatternDetail:
    pattern_id: str
    code: str
    count: int

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "PatternDetail":
        return cls(
            pattern_id=str(data.get("pattern_id", "")),
            code=str(data.get("code", "")).strip().upper(),
            count=int(data.get("count", 0)),
        )


@dataclass
class InventoryLog:
    type: str
    code: str
    change: int
    source: str
    time: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "InventoryLog":
        return cls(
            type=str(data.get("type", "")),
            code=str(data.get("code", "")).strip().upper(),
            change=int(data.get("change", 0)),
            source=str(data.get("source", "")),
            time=str(data.get("time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))),
        )


@dataclass
class RecognitionResult:
    pattern_name: str
    beads: list = field(default_factory=list)  # [{"code": "A1", "count": 42}, ...]

    @classmethod
    def from_dict(cls, data: dict) -> "RecognitionResult":
        beads = []
        for b in data.get("beads", []):
            beads.append({
                "code": str(b.get("code", "")).strip().upper(),
                "count": int(b.get("count", 0)),
            })
        return cls(
            pattern_name=str(data.get("pattern_name", "未知图纸")),
            beads=beads,
        )

    @classmethod
    def from_list(cls, data: list) -> "RecognitionResult":
        """Parse from a list format: [{"code":"A1","count":42}, ...]"""
        beads = []
        for b in data:
            beads.append({
                "code": str(b.get("code", "")).strip().upper(),
                "count": int(b.get("count", 0)),
            })
        return cls(pattern_name="未知图纸", beads=beads)
