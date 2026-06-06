from repositories.revenue_kpi_repository import (
    RevenueKPIRepository
)

df = RevenueKPIRepository.get_all()

print(df)
print(df.columns.tolist())