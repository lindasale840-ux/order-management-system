from repositories.external_expense_repository import (
    ExternalExpenseRepository
)

from repositories.log_repository import (
    LogRepository
)


class ExternalExpenseService:

    @staticmethod
    def add_expense(

        expense_date,

        amount,

        note
    ):

        ExternalExpenseRepository.add_expense(

            expense_date,

            amount,

            note
        )

        LogRepository.add_log(

            "ADD_EXPENSE",

            "",

            "",

            f"""
            expense_date={expense_date}
            amount={amount}
            note={note}
            """
        )
    @staticmethod
    def delete_expense(
        expense_id
    ):

        ExternalExpenseRepository.delete_expense(
            expense_id
        )

        LogRepository.add_log(

            "DELETE_EXPENSE",

            "",

            "",

            f"Delete expense id={expense_id}"
        )     