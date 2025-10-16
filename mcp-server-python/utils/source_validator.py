from typing import Dict, Any
from pydantic import ValidationError
from schemas.schemas import OutlookMetadata, SnowflakeMetadata, BoxMetadata


class SourceValidator:
    """Validator for source metadata based on source type."""
    
    @staticmethod
    def validate_metadata(source_type: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate metadata based on source type.
        Returns validated metadata dict.
        Raises ValidationError if invalid.
        """
        if source_type == "outlook":
            validated = OutlookMetadata(**metadata)
            return validated.model_dump()
        elif source_type == "snowflake":
            validated = SnowflakeMetadata(**metadata)
            return validated.model_dump()
        elif source_type == "box":
            validated = BoxMetadata(**metadata)
            return validated.model_dump()
        else:
            raise ValueError(f"Unsupported source type: {source_type}")
