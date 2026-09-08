"""
Phase 7: Reports & Analytics
Report generation and analytics dashboard
"""
import logging
from typing import Dict, List
from sqlalchemy.orm import Session
from datetime import datetime
import json

from models import Report, ExtractedRecord, Document, Topic
from validation import ValidationService

logger = logging.getLogger(__name__)


class ReportService:
    """Service for generating reports"""

    @staticmethod
    def generate_production_report(
        db: Session,
        subsidiary: str = None,
        mine: str = None,
        financial_year: str = None,
        include_trends: bool = True,
        include_target_vs_actual: bool = True,
        include_anomalies: bool = False,
    ) -> Dict:
        """
        Generate a production report with optional filters

        Returns:
            {
                "report_id": int,
                "title": str,
                "content": str,
                "tables": [...],
                "charts": [...],
                "generated_at": str
            }
        """
        try:
            # Build query
            query = db.query(ExtractedRecord)

            if subsidiary:
                query = query.filter(ExtractedRecord.subsidiary == subsidiary)
            if mine:
                query = query.filter(ExtractedRecord.mine == mine)
            if financial_year:
                query = query.filter(ExtractedRecord.financial_year == financial_year)

            records = query.all()

            if not records:
                return {
                    "title": "Production Report",
                    "content": "No data available for selected filters",
                    "error": "No records found"
                }

            # Build report content
            content = f"# Production Report\n"
            content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

            if subsidiary:
                content += f"**Subsidiary:** {subsidiary}\n"
            if mine:
                content += f"**Mine:** {mine}\n"
            if financial_year:
                content += f"**Financial Year:** {financial_year}\n"

            content += "\n## Summary Statistics\n"

            # Calculate totals
            total_production = sum(r.production_value for r in records if r.production_value)
            total_target = sum(r.target_value for r in records if r.target_value)
            avg_achievement = (total_production / total_target * 100) if total_target else 0

            content += f"- **Total Production:** {total_production:.2f}\n"
            content += f"- **Total Target:** {total_target:.2f}\n"
            content += f"- **Achievement:** {avg_achievement:.1f}%\n"
            content += f"- **Records:** {len(records)}\n"

            # Production by entity
            if include_target_vs_actual:
                content += "\n## Production vs Target\n"
                content += "| Subsidiary | Mine | Year | Production | Target | Achievement |\n"
                content += "|---|---|---|---|---|---|\n"

                for record in records:
                    if record.production_value and record.target_value:
                        achievement = (record.production_value / record.target_value * 100)
                        content += f"| {record.subsidiary} | {record.mine} | {record.financial_year} | "
                        content += f"{record.production_value} | {record.target_value} | {achievement:.1f}% |\n"

            # Anomalies
            if include_anomalies:
                content += "\n## Anomalies Detected\n"
                anomalies = ValidationService.flag_anomalies(db)
                if anomalies:
                    for anomaly in anomalies[:10]:  # Top 10
                        content += f"- **{anomaly['type']}**: Record ID {anomaly['record_id']}\n"
                else:
                    content += "No anomalies detected.\n"

            # Confidence
            avg_confidence = sum(r.confidence_score for r in records if r.confidence_score) / len(records) if records else 0
            content += f"\n## Data Quality\n"
            content += f"- **Average Confidence:** {avg_confidence * 100:.1f}%\n"
            content += f"- **Verified Records:** {len([r for r in records if r.validation_status == 'verified'])}\n"

            # Store report
            report = Report(
                title=f"Production Report - {subsidiary or 'All'} {mine or ''} {financial_year or ''}",
                report_type="production",
                filters={
                    "subsidiary": subsidiary,
                    "mine": mine,
                    "financial_year": financial_year,
                },
                content=content,
            )
            db.add(report)
            db.commit()
            db.refresh(report)

            logger.info(f"Generated production report {report.id}")

            return {
                "report_id": report.id,
                "title": report.title,
                "content": content,
                "generated_at": report.generated_at.isoformat(),
            }

        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return {
                "title": "Production Report",
                "content": f"Error generating report: {str(e)}",
                "error": str(e)
            }

    @staticmethod
    def get_production_trends(
        db: Session,
        subsidiary: str = None,
        mine: str = None,
        limit: int = 10,
    ) -> List[Dict]:
        """
        Get production trends over time

        Returns sorted list of (year, production) tuples
        """
        query = db.query(ExtractedRecord)

        if subsidiary:
            query = query.filter(ExtractedRecord.subsidiary == subsidiary)
        if mine:
            query = query.filter(ExtractedRecord.mine == mine)

        records = query.order_by(ExtractedRecord.financial_year).all()

        trends = {}
        for record in records:
            if record.financial_year and record.production_value:
                year = record.financial_year
                if year not in trends:
                    trends[year] = 0
                trends[year] += record.production_value

        return [{"year": year, "production": prod} for year, prod in sorted(trends.items())]


class AnalyticsService:
    """Service for analytics and dashboards"""

    @staticmethod
    def get_dashboard_metrics(db: Session) -> Dict:
        """Get all dashboard metrics"""
        return {
            "documents": {
                "total": db.query(Document).count(),
                "processed": db.query(Document).filter(Document.status == "processed").count(),
                "failed": db.query(Document).filter(Document.status == "failed").count(),
            },
            "extraction": {
                "total_records": db.query(ExtractedRecord).count(),
                "verified": db.query(ExtractedRecord).filter(
                    ExtractedRecord.validation_status == "verified"
                ).count(),
                "with_warnings": db.query(ExtractedRecord).filter(
                    ExtractedRecord.validation_status == "warning"
                ).count(),
            },
            "quality": {
                "avg_confidence": db.query(ExtractedRecord).filter(
                    ExtractedRecord.confidence_score.isnot(None)
                ).count(),
                "high_confidence": db.query(ExtractedRecord).filter(
                    ExtractedRecord.confidence_score >= 0.8
                ).count(),
            }
        }

    @staticmethod
    def get_production_summary(db: Session) -> Dict:
        """Get production summary across all data"""
        records = db.query(ExtractedRecord).filter(
            ExtractedRecord.production_value.isnot(None)
        ).all()

        if not records:
            return {"total": 0, "average": 0, "min": 0, "max": 0}

        values = [r.production_value for r in records]
        return {
            "total": sum(values),
            "average": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "count": len(values),
        }

    @staticmethod
    def get_target_achievement(db: Session) -> Dict:
        """Calculate target achievement rates"""
        records = db.query(ExtractedRecord).filter(
            ExtractedRecord.production_value.isnot(None),
            ExtractedRecord.target_value.isnot(None)
        ).all()

        if not records:
            return {"average_achievement": 0, "records": 0}

        achievements = []
        for record in records:
            if record.target_value > 0:
                achievement = (record.production_value / record.target_value) * 100
                achievements.append(achievement)

        return {
            "average_achievement": sum(achievements) / len(achievements) if achievements else 0,
            "above_target": len([a for a in achievements if a >= 100]),
            "below_target": len([a for a in achievements if a < 100]),
            "records": len(achievements),
        }

    @staticmethod
    def get_subsidiary_comparison(db: Session) -> List[Dict]:
        """Get production comparison across subsidiaries"""
        records = db.query(ExtractedRecord).filter(
            ExtractedRecord.production_value.isnot(None)
        ).all()

        subsidiaries = {}
        for record in records:
            if record.subsidiary:
                if record.subsidiary not in subsidiaries:
                    subsidiaries[record.subsidiary] = {
                        "production": 0,
                        "target": 0,
                        "count": 0
                    }
                subsidiaries[record.subsidiary]["production"] += record.production_value
                if record.target_value:
                    subsidiaries[record.subsidiary]["target"] += record.target_value
                subsidiaries[record.subsidiary]["count"] += 1

        result = []
        for subsidiary, data in subsidiaries.items():
            achievement = (data["production"] / data["target"] * 100) if data["target"] > 0 else 0
            result.append({
                "subsidiary": subsidiary,
                "production": round(data["production"], 2),
                "target": round(data["target"], 2),
                "achievement": round(achievement, 1),
                "records": data["count"],
            })

        return sorted(result, key=lambda x: x["production"], reverse=True)

    @staticmethod
    def get_mine_statistics(db: Session) -> List[Dict]:
        """Get statistics by mine"""
        records = db.query(ExtractedRecord).filter(
            ExtractedRecord.production_value.isnot(None)
        ).all()

        mines = {}
        for record in records:
            if record.mine:
                if record.mine not in mines:
                    mines[record.mine] = {
                        "production": 0,
                        "count": 0,
                        "subsidiary": record.subsidiary,
                    }
                mines[record.mine]["production"] += record.production_value
                mines[record.mine]["count"] += 1

        result = []
        for mine, data in mines.items():
            avg_production = data["production"] / data["count"]
            result.append({
                "mine": mine,
                "subsidiary": data["subsidiary"],
                "total_production": round(data["production"], 2),
                "average_production": round(avg_production, 2),
                "records": data["count"],
            })

        return sorted(result, key=lambda x: x["total_production"], reverse=True)
