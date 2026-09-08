"""
Phase 4: Validation & Standardization
Validates extracted data and detects anomalies
"""
import logging
from typing import Dict, List, Tuple
from sqlalchemy.orm import Session
from models import ExtractedRecord, ValidationResult

logger = logging.getLogger(__name__)

# Unit conversion mapping
UNIT_CONVERSIONS = {
    "mt": 1.0,  # Metric ton (base)
    "metric ton": 1.0,
    "metric tons": 1.0,
    "ton": 0.907185,  # US ton to MT
    "tons": 0.907185,
    "t": 1.0,  # Often MT
    "kg": 0.001,  # Kilogram to MT
    "kilograms": 0.001,
}

# Normal production ranges (MT)
PRODUCTION_RANGES = {
    "coal": (0.1, 500),  # Typical coal mine production
    "iron": (1, 1000),
    "copper": (0.01, 100),
    "default": (0.1, 1000),
}


class ValidationService:
    """Service for data validation and standardization"""

    @staticmethod
    def normalize_unit(value: float, unit: str) -> Tuple[float, str]:
        """
        Normalize unit to metric tons

        Args:
            value: Numeric value
            unit: Unit string

        Returns:
            (normalized_value, "MT")
        """
        if value is None or unit is None:
            return None, None

        unit_lower = unit.lower().strip()
        conversion = UNIT_CONVERSIONS.get(unit_lower, None)

        if conversion is None:
            logger.warning(f"Unknown unit: {unit}")
            return value, unit

        normalized = value * conversion
        return round(normalized, 2), "MT"

    @staticmethod
    def validate_record(db: Session, record: ExtractedRecord) -> List[Dict]:
        """
        Validate a single extracted record

        Returns list of validation issues:
            [{
                "validation_type": str,
                "status": "pass" | "warning" | "fail",
                "message": str
            }, ...]
        """
        issues = []

        # Check required fields
        if not record.financial_year:
            issues.append({
                "validation_type": "required_field",
                "status": "warning",
                "message": "Missing financial year"
            })

        if not record.subsidiary:
            issues.append({
                "validation_type": "required_field",
                "status": "warning",
                "message": "Missing subsidiary name"
            })

        # Validate production values
        if record.production_value is not None:
            if record.production_value <= 0:
                issues.append({
                    "validation_type": "value_range",
                    "status": "fail",
                    "message": f"Invalid production value: {record.production_value}"
                })
            elif record.production_value > 10000:
                issues.append({
                    "validation_type": "anomaly",
                    "status": "warning",
                    "message": f"Unusually high production: {record.production_value} {record.production_unit}"
                })

        # Validate target vs production
        if record.production_value and record.target_value:
            if record.production_value > record.target_value * 2:
                issues.append({
                    "validation_type": "target_deviation",
                    "status": "warning",
                    "message": f"Production {record.production_value} exceeds target {record.target_value} by >100%"
                })
            elif record.production_value < record.target_value * 0.5:
                issues.append({
                    "validation_type": "target_deviation",
                    "status": "warning",
                    "message": f"Production {record.production_value} is <50% of target {record.target_value}"
                })

        # Normalize units
        if record.production_unit:
            normalized_val, normalized_unit = ValidationService.normalize_unit(
                record.production_value,
                record.production_unit
            )
            if normalized_unit != record.production_unit:
                issues.append({
                    "validation_type": "unit_normalization",
                    "status": "pass",
                    "message": f"Unit normalized from {record.production_unit} to {normalized_unit}"
                })

        # Check for duplicates
        duplicates = db.query(ExtractedRecord).filter(
            ExtractedRecord.id != record.id,
            ExtractedRecord.source_document_id != record.source_document_id,
            ExtractedRecord.subsidiary == record.subsidiary,
            ExtractedRecord.mine == record.mine,
            ExtractedRecord.financial_year == record.financial_year,
        ).all()

        if duplicates:
            issues.append({
                "validation_type": "duplicate_detection",
                "status": "warning",
                "message": f"Potential duplicate data from {len(duplicates)} other documents"
            })

        return issues

    @staticmethod
    def validate_document(db: Session, document_id: int) -> Dict:
        """
        Validate all records for a document

        Returns:
            {
                "total_records": int,
                "passed": int,
                "warnings": int,
                "failed": int,
                "issues": [...]
            }
        """
        records = db.query(ExtractedRecord).filter(
            ExtractedRecord.source_document_id == document_id
        ).all()

        all_issues = []
        passed = 0
        warnings = 0
        failed = 0

        for record in records:
            issues = ValidationService.validate_record(db, record)

            # Determine status
            has_fail = any(i["status"] == "fail" for i in issues)
            has_warning = any(i["status"] == "warning" for i in issues)

            if has_fail:
                status = "fail"
                failed += 1
            elif has_warning:
                status = "warning"
                warnings += 1
            else:
                status = "pass"
                passed += 1

            record.validation_status = status

            # Store validation results
            for issue in issues:
                val_result = ValidationResult(
                    record_id=record.id,
                    validation_type=issue["validation_type"],
                    status=issue["status"],
                    message=issue["message"],
                    resolved=0,
                )
                db.add(val_result)
                all_issues.append(issue)

        db.commit()

        logger.info(f"Validation complete: {passed} passed, {warnings} warnings, {failed} failed")

        return {
            "total_records": len(records),
            "passed": passed,
            "warnings": warnings,
            "failed": failed,
            "issues": all_issues,
        }

    @staticmethod
    def cross_check_values(db: Session, subsidiary: str, mine: str, financial_year: str) -> Dict:
        """
        Cross-check production values across documents

        Returns:
            {
                "records": [...],
                "consensus_value": float,
                "variance": float,
                "status": "verified" | "discrepancy"
            }
        """
        records = db.query(ExtractedRecord).filter(
            ExtractedRecord.subsidiary == subsidiary,
            ExtractedRecord.mine == mine,
            ExtractedRecord.financial_year == financial_year,
        ).all()

        if not records:
            return {"status": "no_data"}

        if len(records) == 1:
            return {
                "status": "single_source",
                "records": [{"value": records[0].production_value, "source": records[0].source_document_id}],
                "consensus_value": records[0].production_value,
            }

        # Multiple records - check consistency
        values = [r.production_value for r in records if r.production_value]

        if not values:
            return {"status": "no_values"}

        avg = sum(values) / len(values)
        variance = max(values) - min(values)
        variance_pct = (variance / avg * 100) if avg else 0

        status = "verified" if variance_pct < 5 else "discrepancy"

        logger.info(f"Cross-check: {subsidiary}/{mine}/{financial_year} - variance: {variance_pct}%")

        return {
            "status": status,
            "records": [{"value": r.production_value, "source": r.source_document_id} for r in records],
            "consensus_value": round(avg, 2),
            "variance": round(variance, 2),
            "variance_pct": round(variance_pct, 2),
        }

    @staticmethod
    def flag_anomalies(db: Session) -> List[Dict]:
        """
        Find anomalous records system-wide

        Returns list of anomalies
        """
        anomalies = []

        # Find very high/low production values
        records = db.query(ExtractedRecord).filter(
            ExtractedRecord.production_value.isnot(None)
        ).all()

        for record in records:
            if record.production_value and record.production_value > 5000:
                anomalies.append({
                    "record_id": record.id,
                    "type": "unusually_high_production",
                    "value": record.production_value,
                    "unit": record.production_unit,
                })
            elif record.production_value and record.production_value < 0.01:
                anomalies.append({
                    "record_id": record.id,
                    "type": "unusually_low_production",
                    "value": record.production_value,
                    "unit": record.production_unit,
                })

        # Find records with large deviations from target
        for record in records:
            if record.target_value and record.production_value:
                deviation = abs(record.production_value - record.target_value) / record.target_value
                if deviation > 0.5:  # >50% deviation
                    anomalies.append({
                        "record_id": record.id,
                        "type": "large_target_deviation",
                        "production": record.production_value,
                        "target": record.target_value,
                        "deviation_pct": round(deviation * 100, 1),
                    })

        logger.info(f"Found {len(anomalies)} anomalies")
        return anomalies
