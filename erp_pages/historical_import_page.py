import streamlit as st
import pandas as pd
from io import BytesIO

from openpyxl.styles import (
    Font,
    PatternFill,
    Alignment
)

from openpyxl.worksheet.datavalidation import (
    DataValidation
)

from openpyxl.utils import get_column_letter

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
    
    columns = [

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

    df = pd.DataFrame(columns=columns)

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        # =====================
        # IMPORT SHEET
        # =====================

        df.to_excel(

            writer,

            sheet_name="Import",

            index=False
        )

        workbook = writer.book

        ws = writer.sheets["Import"]

        header_fill = PatternFill(

            fill_type="solid",

            start_color="1F4E78"
        )

        header_font = Font(

            color="FFFFFF",

            bold=True
        )

        required_fill = PatternFill(

            fill_type="solid",

            start_color="FFF2CC"
        )

        for cell in ws[1]:

            cell.fill = header_fill

            cell.font = header_font

            cell.alignment = Alignment(

                horizontal="center",

                vertical="center",

                wrap_text=True
            )

        required_cols = [

            "customer_name",

            "order_number",

            "sale_owner"
        ]

        for col_name in required_cols:

            col_index = columns.index(col_name) + 1

            ws.cell(
                row=2,
                column=col_index
            ).fill = required_fill

        sample_row = [

            "ABC Company",

            "GST001",

            "2026-06-01",

            "2026-06-05",

            "LINDA",

            "INV001",

            "2026-06-10",

            30,

            "2026-07-05",

            5000000,

            10,

            500000,

            "Historical import example"
        ]

        for col_num, value in enumerate(
            sample_row,
            start=1
        ):

            ws.cell(
                row=2,
                column=col_num
            ).value = value

        ws.freeze_panes = "A2"

        ws.auto_filter.ref = ws.dimensions

        for column_cells in ws.columns:

            length = max(

                len(str(cell.value))
                if cell.value
                else 0

                for cell in column_cells
            )

            adjusted_width = min(
                length + 5,
                40
            )

            ws.column_dimensions[
                get_column_letter(
                    column_cells[0].column
                )
            ].width = adjusted_width

        payment_terms_validation = DataValidation(

            type="list",

            formula1='"30,45,60,90"'
        )

        ws.add_data_validation(
            payment_terms_validation
        )

        payment_terms_validation.add(
            "H2:H5000"
        )

        # =====================
        # INSTRUCTION SHEET
        # =====================

        instruction_ws = workbook.create_sheet(
            "Instruction"
        )

        instruction_ws.append(

            [

                "Field",

                "Required",

                "Description",

                "Example"
            ]
        )

        instructions = [

            ["customer_name","YES","Customer Name","ABC Company"],

            ["order_number","YES","Order Number","GST001"],

            ["measurement_date","NO","Calibration Date","2026-06-01"],

            ["cert_status","NO","Certificate Date","2026-06-05"],

            ["sale_owner","YES","Sales Owner","LINDA"],

            ["invoice_group","NO","Invoice Group","INV001"],

            ["invoice_date","NO","Invoice Date","2026-06-10"],

            ["payment_terms","NO","Payment Term","30"],

            ["payment_status","NO","Paid Date","2026-07-05"],

            ["total","NO","Revenue","5000000"],

            ["commission_percent","NO","Commission %","10"],

            ["commission_actual","NO","Commission Amount","500000"],

            ["note","NO","Remark","Historical import"]
        ]

        for row in instructions:

            instruction_ws.append(row)

        for cell in instruction_ws[1]:

            cell.fill = header_fill

            cell.font = header_font

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

            # =========================
            # DATE FIELDS
            # =========================

            measurement_date = None

            if pd.notna(
                row.get("measurement_date")
            ):
                measurement_date = (
                    pd.to_datetime(
                        row.get("measurement_date")
                    )
                    .date()
                    .isoformat()
                )

            cert_status = None

            if pd.notna(
                row.get("cert_status")
            ):
                cert_status = (
                    pd.to_datetime(
                        row.get("cert_status")
                    )
                    .date()
                    .isoformat()
                )

            invoice_date = None

            if pd.notna(
                row.get("invoice_date")
            ):
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