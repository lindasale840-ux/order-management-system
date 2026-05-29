import pandas as pd

from services.finance_service import (
    FinanceService
)

class ChartService:

    @staticmethod
    def revenue_by_customer():

        df = (
            FinanceService
            .build_finance_dataframe()
        )

        result = (
            df.groupby("customer_name")["total"]
            .sum()
            .reset_index()
        )

        return result

    @staticmethod
    def monthly_revenue():

        df = (
            FinanceService
            .build_finance_dataframe()
        )

        df["invoice_date"] = pd.to_datetime(
            df["invoice_date"]
        )

        df["month"] = (
            df["invoice_date"]
            .dt.strftime("%Y-%m")
        )

        result = (
            df.groupby("month")["total"]
            .sum()
            .reset_index()
        )

        return result