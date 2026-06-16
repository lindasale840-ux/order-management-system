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

from services.dashboard_service import (
    DashboardService
)

from services.payment_service import (
    PaymentService
)

from repositories.user_repository import (
    UserRepository
)


def generate_template():
    
    columns = [

        "customer_name",
        "order_number",
        "measurement_date",
        "cert_status",
        "sale_owner",
        "created_by",

        "invoice_group",
        "invoice_date",
        "payment_terms",
        "payment_status",

        "total",
        "commission_percent",

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

            "Thịnh",

            "INV001",

            "2026-06-10",

            30,

            "2026-07-05",

            5000000,

            10,

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
            "I2:I5000"
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
            
            ["created_by","YES","Assistant Owner","Thịnh"],

            ["invoice_group","NO","Invoice Group","INV001"],

            ["invoice_date","NO","Invoice Date","2026-06-10"],

            ["payment_terms","NO","Payment Term","30"],

            ["payment_status","NO","Paid Date","2026-07-05"],

            ["total","NO","Revenue","5000000"],

            ["commission_percent","NO","Commission %","10"],

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
    
    validation_errors = []
    
    if st.button("🔍 Validate File"):

        if df["customer_name"].isna().any():
            validation_errors.append("Missing customer_name")

        if df["order_number"].isna().any():
            validation_errors.append("Missing order_number")

        if df["sale_owner"].isna().any():
            validation_errors.append("Missing sale_owner")

        if "created_by" in df.columns:

            if df["created_by"].isna().any():
                validation_errors.append("Missing created_by")

        duplicates = df[
            df["order_number"]
            .duplicated(keep=False)
        ]

        if not duplicates.empty:

            validation_errors.append(
                f"Duplicate order_number found: {duplicates['order_number'].tolist()}"
            )

        invalid_commission = df[
            df["commission_percent"] > 100
        ]

        if not invalid_commission.empty:

            validation_errors.append(
                "Commission percent > 100"
            )
            
        invalid_payment_terms = df[
            df["payment_terms"].fillna(0) > 365
        ]

        if not invalid_payment_terms.empty:

            validation_errors.append(
                "Payment Terms > 365"
            )
            
        users_df = UserRepository.get_all_users()

        valid_users = users_df["username"].tolist()

        invalid_created_by = df[
            ~df["created_by"].isin(valid_users)
        ]

        if not invalid_created_by.empty:

            validation_errors.append(
                "Invalid created_by username found"
            )        

        if validation_errors:

            st.error("Validation Failed")

            for err in validation_errors:

                st.write("❌", err)

        else:

            st.success("Validation Passed")

    confirm_import = st.checkbox(
        "I confirm importing historical data"
    )
    
    if st.button(
        "🚀 Import To ERP"
    ):

        if not confirm_import:

            st.error(
                "Please confirm first"
            )

            st.stop()

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

            created_by = (

                row.get("created_by")

                if pd.notna(
                    row.get("created_by")
                )

                else st.session_state["username"]

            )
            
            print(
                "measurement_date =",
                measurement_date
            )

            DashboardService.sync_order(

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
                ),

                created_by=created_by

            )

            imported_orders += 1
            
            # =========================
            # LOG
            # =========================
            
           # LogRepository.add_log(

            #    "HISTORICAL_IMPORT",

             #   row.get(
             #       "customer_name"
              #  ),

               # row.get(
                #    "order_number"
               # ),

                #"Historical import"

           # )

            # =========================
            # PAYMENT
            # =========================
            
            total = float(
                row.get("total", 0) or 0
            )

            commission_percent = float(
                row.get(
                    "commission_percent",
                    0
                ) or 0
            )

            commission_actual = (

                total

                *

                commission_percent

                / 100

            )
            
            payment_terms = row.get("payment_terms", 0)

            if pd.isna(payment_terms):
                payment_terms = 0
                        
            PaymentService.save_invoice(

                order_number=row.get(
                    "order_number"
                ),

                invoice_date=invoice_date,

                invoice_group=row.get(
                    "invoice_group"
                ),

                payment_terms=payment_terms,

                payment_status=payment_status,

                total=total,

                commission_percent=commission_percent,

                note=row.get(
                    "note"
                ),

                invoice_created_by=created_by

            )

            imported_payments += 1

        st.cache_data.clear()
        
        st.success(

            f"""
            Imported:

            Orders: {imported_orders}

            Payments: {imported_payments}
            """
        )
        
        st.rerun()