from repositories.revenue_kpi_repository import (
    RevenueKPIRepository
)

RevenueKPIRepository.upsert_kpi(

    2026,
    6,
    150000000

)

print(
    RevenueKPIRepository.get_all()
)