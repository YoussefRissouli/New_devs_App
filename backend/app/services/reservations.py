from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

async def calculate_total_revenue(property_id: str, tenant_id: str, month: int, year: int) -> Dict[str, Any]:
    """
    Aggregates revenue from database.
    """
    try:
        from app.core.database_pool import db_pool
        
        await db_pool.initialize()
        
        if db_pool.session_factory:
            async with db_pool.get_session() as session:
                from sqlalchemy import text

                timezone_result = await session.execute(
                    text("""
                        SELECT timezone
                        FROM properties
                        WHERE id = :property_id AND tenant_id = :tenant_id
                    """),
                    {"property_id": property_id, "tenant_id": tenant_id},
                )
                property_timezone = timezone_result.scalar_one_or_none()

                if not property_timezone:
                    return {
                        "property_id": property_id,
                        "tenant_id": tenant_id,
                        "total": "0.00",
                        "currency": "USD",
                        "count": 0,
                    }

                try:
                    timezone = ZoneInfo(property_timezone)
                except ZoneInfoNotFoundError as exc:
                    raise RuntimeError("Property timezone is invalid") from exc

                start_date = datetime(year, month, 1, tzinfo=timezone)
                end_date = (
                    datetime(year + 1, 1, 1, tzinfo=timezone)
                    if month == 12
                    else datetime(year, month + 1, 1, tzinfo=timezone)
                )

                query = text("""
                    SELECT 
                        property_id,
                        SUM(total_amount) as total_revenue,
                        COUNT(*) as reservation_count
                    FROM reservations 
                    WHERE property_id = :property_id
                        AND tenant_id = :tenant_id
                        AND check_in_date >= :start_date
                        AND check_in_date < :end_date
                    GROUP BY property_id
                """)
                
                result = await session.execute(query, {
                    "property_id": property_id, 
                    "tenant_id": tenant_id,
                    "start_date": start_date,
                    "end_date": end_date,
                })
                row = result.fetchone()
                
                if row:
                    total_revenue = Decimal(str(row.total_revenue)).quantize(
                        Decimal("0.01"),
                        rounding=ROUND_HALF_UP,
                    )
                    return {
                        "property_id": property_id,
                        "tenant_id": tenant_id,
                        "total": str(total_revenue),
                        "currency": "USD", 
                        "count": row.reservation_count
                    }
                else:
                    # No reservations found for this property
                    return {
                        "property_id": property_id,
                        "tenant_id": tenant_id,
                        "total": "0.00",
                        "currency": "USD",
                        "count": 0
                    }
        else:
            raise Exception("Database pool not available")
            
    except Exception as exc:
        raise RuntimeError("Revenue data is unavailable") from exc
