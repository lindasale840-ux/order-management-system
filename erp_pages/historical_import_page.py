import streamlit as st
import pandas as pd
from io import BytesIO

from utils.auth_guard import (
    require_admin
)

from repositories.order_repository import (
    OrderRepository
)

from repositories.payment_repository import (
    PaymentRepository
)

def generate_template():

    df = pd.DataFrame(

        columns=[

            "customer_name",

            "order_number",

            "measurement_date",

            "cert_status",

            "sale_owner",

            "invoice_group",

            "invoice_date",

            "payment_terms",

            "payment_status",

            "total",

            "commission_percent",

            "commission_actual",

            "note"
        ]
    )

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        df.to_excel(

            writer,

            sheet_name="Import",

            index=False
        )

    return output.getvalue()


def show_historical_import_page():

    require_admin()

    st.title(
        "📥 Historical Data Import"
    )

    template_data = generate_template()

    st.download_button(

        label="📥 Download Import Template",

        data=template_data,

        file_name="ERP_Import_Template.xlsx",

        mime=(
            "application/vnd.openxmlformats-"
            "officedocument.spreadsheetml.sheet"
        )
    )

    uploaded_file = st.file_uploader(

        "Upload Historical Excel",

        type=["xlsx"]
    )

    if uploaded_file is None:

        st.info(
            "Please upload Excel file."
        )

        return

    df = pd.read_excel(
        uploaded_file
    )

    st.success(
        f"{len(df)} rows loaded"
    )

    st.dataframe(
        df,
        use_container_width=True
    )

    if st.button(
        "🚀 Import To ERP"
    ):

        imported_orders = 0
        imported_payments = 0

        for _, row in df.iterrows():

            measurement_date = None
        if pd.notna(row.get("measurement_date")):
            measurement_date = (
                pd.to_datetime(
                    row.get("measurement_date")
                )
                .date()
                .isoformat()
            )

        cert_status = None
        if pd.notna(row.get("cert_status")):
            cert_status = (
                pd.to_datetime(
                    row.get("cert_status")
                )
                .date()
                .isoformat()
            )

        invoice_date = None
        if pd.notna(row.get("invoice_date")):
            invoice_date = (
                pd.to_datetime(
                    row.get("invoice_date")
                )
                .date()
                .isoformat()
            )

        payment_status = None

        if pd.notna(
            row.get("payment_status")
        ):
            payment_status = str(
                row.get("payment_status")
            )

            # =========================
            # ORDER
            # =========================

            OrderRepository.upsert_order(

                customer_name=row.get(
                    "customer_name"
                ),

                order_number=row.get(
                    "order_number"
                ),

                measurement_date=measurement_date,

                cert_status=cert_status,

                sale_owner=row.get(
                    "sale_owner"
                )
            )

            imported_orders += 1

            # =========================
            # PAYMENT
            # =========================

            PaymentRepository.upsert_payment(

                order_number=row.get(
                    "order_number"
                ),

                invoice_date=invoice_date,

                invoice_group=row.get(
                    "invoice_group"
                ),

                payment_terms=row.get(
                    "payment_terms"
                ),

                payment_status=payment_status,

                total=row.get(
                    "total"
                ),

                commission_percent=row.get(
                    "commission_percent"
                ),

                commission_actual=row.get(
                    "commission_actual"
                ),

                note=row.get(
                    "note"
                )
            )

            imported_payments += 1

        st.success(

            f"""
            Imported:

            Orders: {imported_orders}

            Payments: {imported_payments}
            """
        )