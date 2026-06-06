from repositories.revenue_kpi_repository import (
    RevenueKPIRepository
)

from repositories.log_repository import (
    LogRepository
)


class RevenueKPIService:

    @staticmethod
    def upsert_kpi(

        year,
        month,
        target_amount

    ):

        RevenueKPIRepository.upsert_kpi(

            year,
            month,
            target_amount

        )

        LogRepository.add_log(

            "UPSERT_REVENUE_KPI",

            "",

            "",

            f"""

            year={year}
            month={month}
            target={target_amount}

            """

        )

    @staticmethod
    def delete_kpi(

        kpi_id

    ):

        RevenueKPIRepository.delete_kpi(

            kpi_id

        )

        LogRepository.add_log(

            "DELETE_REVENUE_KPI",

            "",

            "",

            f"id={kpi_id}"

        )