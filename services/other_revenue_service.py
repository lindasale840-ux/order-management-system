from repositories.other_revenue_repository import (
    OtherRevenueRepository
)

from repositories.log_repository import (
    LogRepository
)


class OtherRevenueService:

    @staticmethod
    def add_revenue(

        revenue_date,

        amount,

        note
    ):

        OtherRevenueRepository.add_revenue(

            revenue_date,

            amount,

            note
        )

        LogRepository.add_log(

            "ADD_OTHER_REVENUE",

            "",

            "",

            f"""
            revenue_date={revenue_date}
            amount={amount}
            note={note}
            """
        )

    @staticmethod
    def delete_revenue(
        revenue_id
    ):

        OtherRevenueRepository.delete_revenue(
            revenue_id
        )

        LogRepository.add_log(

            "DELETE_OTHER_REVENUE",

            "",

            "",

            f"Delete revenue id={revenue_id}"
        )