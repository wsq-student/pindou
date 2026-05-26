from models.models import PatternRecord, PatternDetail, RecognitionResult
from storage.pattern_store import PatternStore
from utils.logger import get_logger

logger = get_logger(__name__)


class PatternService:
    def __init__(self):
        self.store = PatternStore()

    def save_recognition(
        self, image_path: str, result: RecognitionResult
    ) -> str:
        pattern_id = self.store.save_pattern(
            pattern_name=result.pattern_name,
            image_path=str(image_path),
            beads=result.beads,
        )
        logger.info(f"保存图纸记录: {result.pattern_name} (ID: {pattern_id})")
        return pattern_id

    def get_all_records(self) -> list[PatternRecord]:
        return self.store.get_all_records()

    def get_details(self, pattern_id: str) -> list[PatternDetail]:
        return self.store.get_details(pattern_id)

    def delete_pattern(self, pattern_id: str) -> bool:
        return self.store.delete_pattern(pattern_id)
