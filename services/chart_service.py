import pandas as pd

from services.finance_service import (
    FinanceService
)
import streamlit as st
class ChartService:

    @staticmethod
    def revenue_by_customer():

        df = FinanceService.build_finance_dataframe(
            role=st.session_state.get("role"),
            username=st.session_state.get("username"),
            sale_owner=st.session_state.get("sale_owner")
        )

        result = (
            df.groupby("customer_name")["total"]
            .sum()
            .reset_index()
        )

        return result

    @staticmethod
    def monthly_revenue():

        df = FinanceService.build_finance_dataframe(
            role=st.session_state.get("role"),
            username=st.session_state.get("username"),
            sale_owner=st.session_state.get("sale_owner")
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