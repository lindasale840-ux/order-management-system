import pandas as pd

import streamlit as st

from repositories.order_repository import (
    OrderRepository
)

from repositories.payment_repository import (
    PaymentRepository
)

from utils.data_permission import (
    filter_by_sale_owner
)


class FinanceService:

    @staticmethod
    @st.cache_data(ttl=60)
    def build_finance_dataframe():

        print(
            "FinanceService.build_finance_dataframe() called"
        )

        orders_df = (
            OrderRepository.get_all_orders()
        )

        orders_df = filter_by_sale_owner(
            orders_df
        )

        payments_df = (
            PaymentRepository.get_all_payments()
        )

        df = pd.merge(

            orders_df,

            payments_df,

            on="order_number",

            how="left",

            suffixes=(
                "_order",
                "_payment"
            )
        )

        today = pd.Timestamp.today()
        
        df["payment_terms"] = pd.to_numeric(
            df["payment_terms"],
            errors="coerce"
        ).fillna(0)

        df["measurement_date"] = pd.to_datetime(
            df["measurement_date"],
            errors="coerce"
        )

        df["cert_status"] = pd.to_datetime(
            df["cert_status"],
            errors="coerce"
        )

        df["invoice_date"] = pd.to_datetime(
            df["invoice_date"],
            errors="coerce"
        )

        df["payment_status"] = pd.to_datetime(
            df["payment_status"],
            errors="coerce"
        )

        order_status_list = []

        payment_overdue_list = []

        payment_status_text_list = []

        cert_overdue_list = []

        cert_due_soon_list = []

        cert_workflow_status_list = []

        for _, row in df.iterrows():

            # =========================
            # ORDER STATUS
            # =========================

            if (
                pd.isna(row["invoice_date"])
                and
                pd.notna(row["cert_status"])
                and
                (today - row["cert_status"]).days > 5
            ):

                order_status = "Missing Invoice"

            else:

                order_status = "OK"

            order_status_list.append(
                order_status
            )

            # =========================
            # PAYMENT OVERDUE
            # =========================

            if pd.notna(
                row["payment_status"]
            ):

                payment_overdue = "No"

            elif pd.isna(
                row["invoice_date"]
            ):

                payment_overdue = "Wait Invoice"

            else:

                due_date = (
                    row["invoice_date"]
                    +
                    pd.Timedelta(
                        days=int(
                            row["payment_terms"]
                        )
                    )
                )

                if today > due_date:

                    payment_overdue = "Overdue"

                else:

                    payment_overdue = "Pending"

            payment_overdue_list.append(
                payment_overdue
            )

            # =========================
            # PAYMENT STATUS TEXT
            # =========================

            if pd.notna(
                row["payment_status"]
            ):

                payment_status_text = "Paid"

            else:

                payment_status_text = "Pending"

            payment_status_text_list.append(
                payment_status_text
            )

            # =========================
            # CERTIFICATE WORKFLOW
            # =========================

            if pd.isna(
                row["cert_status"]
            ):

                if (
                    pd.notna(
                        row["measurement_date"]
                    )
                    and
                    (
                        today
                        -
                        row["measurement_date"]
                    ).days > 5
                ):

                    cert_workflow_status = (
                        "Missing Cert"
                    )

                else:

                    cert_workflow_status = (
                        "Processing Cert"
                    )

            else:

                cert_workflow_status = (
                    "Cert Completed"
                )

            cert_workflow_status_list.append(
                cert_workflow_status
            )

            # =========================
            # CALIBRATION OVERDUE
            # =========================

            if pd.notna(
                row["measurement_date"]
            ):

                calibration_due = (

                    row["measurement_date"]

                    +

                    pd.DateOffset(
                        months=11
                    )
                )

                remaining_days = (

                    calibration_due
                    -
                    today

                ).days

                if remaining_days < 0:

                    cert_overdue = (
                        "Overdue"
                    )

                else:

                    cert_overdue = (
                        "OK"
                    )

                if (
                    0
                    <=
                    remaining_days
                    <=
                    30
                ):

                    cert_due_soon = (
                        "Due Soon"
                    )

                else:

                    cert_due_soon = "No"

            else:

                cert_overdue = "Unknown"

                cert_due_soon = "Unknown"

            cert_overdue_list.append(
                cert_overdue
            )

            cert_due_soon_list.append(
                cert_due_soon
            )

        df["order_status"] = (
            order_status_list
        )

        df["payment_overdue"] = (
            payment_overdue_list
        )

        df["payment_status_text"] = (
            payment_status_text_list
        )

        df["cert_overdue"] = (
            cert_overdue_list
        )

        df["cert_due_soon"] = (
            cert_due_soon_list
        )

        df["cert_workflow_status"] = (
            cert_workflow_status_list
        )

        return df