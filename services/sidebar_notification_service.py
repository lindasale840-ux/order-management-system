from services.finance_service import (
    FinanceService
)

from repositories.document_tracking_repository import (
    DocumentTrackingRepository
)

import pandas as pd


class SidebarNotificationService:

    @staticmethod
    def get_alert_summary():

        df = (
            FinanceService
            .build_finance_dataframe()
        )

        missing_cert = len(

            df[
                df["cert_workflow_status"]
                ==
                "Missing Cert"
            ]
        )

        payment_overdue = len(

            df[
                df["payment_overdue"]
                ==
                "Overdue"
            ]
        )

        due_soon = len(

            df[
                df["cert_due_soon"]
                ==
                "Due Soon"
            ]
        )

        missing_invoice = len(

            df[
                df["order_status"]
                ==
                "Missing Invoice"
            ]
        )

        missing_send = 0
        pending_return = 0

        tracking_df = (
            DocumentTrackingRepository
            .get_latest_tracking()
        )

        today = pd.Timestamp.today()

        # =========================
        # Missing Send
        # =========================

        sent_orders = set()

        if not tracking_df.empty:

            sent_orders = set(
                tracking_df[
                    "order_number"
                ].astype(str)
            )

        cert_orders_df = df[

            df["cert_status"]
            .notna()

        ].copy()

        cert_orders_df["cert_status"] = pd.to_datetime(
            cert_orders_df["cert_status"],
            errors="coerce"
        )

        missing_send_df = cert_orders_df[

            (
                today
                -
                cert_orders_df[
                    "cert_status"
                ]
            ).dt.days.gt(7)

            &

            ~cert_orders_df[
                "order_number"
            ].astype(str).isin(
                sent_orders
            )
        ]

        missing_send = len(
            missing_send_df
        )

        # =========================
        # Pending Return
        # =========================

        if not tracking_df.empty:

            tracking_df["sent_date"] = pd.to_datetime(
                tracking_df["sent_date"],
                errors="coerce"
            )

            tracking_df["received_date"] = pd.to_datetime(
                tracking_df["received_date"],
                errors="coerce"
            )

            pending_return_df = tracking_df[

                tracking_df[
                    "received_date"
                ].isna()

                &

                (
                    today
                    -
                    tracking_df[
                        "sent_date"
                    ]
                ).dt.days.gt(7)
            ]

            pending_return = len(
                pending_return_df
            )

        total_alert = (

            missing_cert

            +

            payment_overdue

            +

            due_soon

            +

            missing_invoice

            +

            missing_send

            +

            pending_return
        )

        return {

            "total": total_alert,

            "missing_cert": missing_cert,

            "payment_overdue": payment_overdue,

            "due_soon": due_soon,

            "missing_invoice": missing_invoice,

            "missing_send": missing_send,

            "pending_return": pending_return
        }