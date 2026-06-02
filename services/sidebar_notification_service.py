from services.finance_service import (
    FinanceService
)

from repositories.document_tracking_repository import (
    DocumentTrackingRepository
)

import pandas as pd


class SidebarNotificationService:

    @staticmethod
    def get_total_alert_count():

        total_alert = 0

        df = (
            FinanceService
            .build_finance_dataframe()
        )

        total_alert += len(

            df[
                df["cert_workflow_status"]
                ==
                "Missing Cert"
            ]
        )

        total_alert += len(

            df[
                df["payment_overdue"]
                ==
                "Overdue"
            ]
        )

        total_alert += len(

            df[
                df["cert_due_soon"]
                ==
                "Due Soon"
            ]
        )

        total_alert += len(

            df[
                df["order_status"]
                ==
                "Missing Invoice"
            ]
        )

        # =====================
        # DOCUMENT TRACKING
        # =====================

        tracking_df = (
            DocumentTrackingRepository
            .get_latest_tracking()
        )

        today = pd.Timestamp.today()

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

            total_alert += len(
                pending_return_df
            )

        return total_alert