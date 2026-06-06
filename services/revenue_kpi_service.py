from repositories.revenue_kpi_repository import (
    RevenueKPIRepository
)


class RevenueKPIService:

    @staticmethod
    def save_kpi(

        year,
        month,
        target_revenue

    ):

        RevenueKPIRepository.upsert_kpi(

            year,
            month,
            target_revenue

        )