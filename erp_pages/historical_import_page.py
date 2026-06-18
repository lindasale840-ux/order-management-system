import streamlit as st
import pandas as pd
from io import BytesIO

import time  # Đảm bảo đã import time ở đầu file để dùng hàm sleep

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

from repositories.order_repository import (
    OrderRepository
)

def generate_template():
    
    columns = [

        "customer_name",
        "order_number",
        "measurement_date",
        "cert_status",
        "sale_owner",
        "created_by",
        
        "disable_calibration_notification",
        "disable_document_notification",

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
            
            0,
            0,

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
            "K2:K5000"
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
            
            ["disable_calibration_notification",
            "NO",
            "0=Track, 1=Disable notification",
            "0"],
            
            [
                "disable_document_notification",
                "NO",
                "0=Track, 1=Disable document notification",
                "0"
            ],

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

    st.title("📥 Historical Data Import")

    template_data = generate_template()

    st.download_button(
        label="📥 Download Import Template",
        data=template_data,
        file_name="ERP_Import_Template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    uploaded_file = st.file_uploader("Upload Historical Excel", type=["xlsx"])

    if uploaded_file is None:
        if "historical_df" in st.session_state:
            del st.session_state["historical_df"]
        st.info("Please upload Excel file.")
        return

    # Lưu chặt vào Session State, không đọc lại file khi rerun
    if "historical_df" not in st.session_state:
        st.session_state["historical_df"] = pd.read_excel(uploaded_file)
        st.success(f"{len(st.session_state['historical_df'])} rows loaded into memory!")

    df = st.session_state["historical_df"]
    
    # Lấy danh sách user chuẩn từ DB để phục vụ hiển thị và validate
    users_df = UserRepository.get_all_users()
    valid_users = users_df["username"].tolist()
    
    # Khu vực xử lý Preview nhanh
    preview_rows = []
    for _, row in df.iterrows():
        order_number = row.get("order_number")
        existing = OrderRepository.get_by_order_number(order_number)
        action = "UPDATE" if not existing.empty else "NEW"

        preview_rows.append({
            "order_number": order_number,
            "customer_name": row.get("customer_name"),
            "sale_owner": row.get("sale_owner"),
            "assistant": row.get("created_by"),
            "action": action
        })

    preview_df = pd.DataFrame(preview_rows)
    
    new_count = len(preview_df[preview_df["action"] == "NEW"])
    update_count = len(preview_df[preview_df["action"] == "UPDATE"])
    total_revenue = pd.to_numeric(df["total"], errors="coerce").fillna(0).sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("NEW Orders", new_count)
    col2.metric("UPDATE Orders", update_count)
    col3.metric("Revenue Import", f"{total_revenue:,.0f}")

    st.subheader("📋 Import Preview")
    st.dataframe(preview_df, use_container_width=True)
    
    # Form đóng băng giao diện
    with st.form(key="import_form_v2"):
        st.markdown("### 🛠️ Import Actions")
        validate_clicked = st.form_submit_button("🔍 Validate File")
        confirm_import = st.checkbox("I confirm importing historical data")
        import_clicked = st.form_submit_button("🚀 Import To ERP")

    # XỬ LÝ VALIDATE
    if validate_clicked:
        validation_errors = []
        if df["customer_name"].isna().any(): validation_errors.append("Missing customer_name")
        if df["order_number"].isna().any(): validation_errors.append("Missing order_number")
        if df["sale_owner"].isna().any(): validation_errors.append("Missing sale_owner")

        duplicates = df[df["order_number"].duplicated(keep=False)]
        if not duplicates.empty:
            validation_errors.append(f"Duplicate order_number found: {duplicates['order_number'].tolist()}")

        # SỬA LỖI USERNAME: Chỉ ra đích danh dòng nào sai và gợi ý username đúng
        invalid_created_by_rows = df[~df["created_by"].astype(str).isin(valid_users)]
        if not invalid_created_by_rows.empty:
            wrong_names = invalid_created_by_rows["created_by"].unique().tolist()
            validation_errors.append(
                f"Invalid username found: {wrong_names}. "
                f"Hệ thống yêu cầu điền chính xác 'username' hệ thống (thường không dấu), không phải tên hiển thị."
            )
            st.info(f"💡 Danh sách Username hợp lệ đang có trên ERP của bạn: `{valid_users}`")

        if validation_errors:
            st.error("Validation Failed")
            for err in validation_errors:
                st.write("❌", err)
        else:
            st.success("Validation Passed! Data hợp lệ 100%.")

    # XỬ LÝ IMPORT CHỐNG TIMEOUT
    if import_clicked:
        if not confirm_import:
            st.error("Please check 'I confirm...' inside the form first!")
            return

        imported_orders = 0
        imported_payments = 0
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        total_rows = len(df)

        for index, row in df.iterrows():
            # TỐI ƯU UI: Cứ mỗi 5 dòng mới cập nhật giao diện một lần để tránh làm nghẽn luồng Streamlit
            if index % 5 == 0 or (index + 1) == total_rows:
                percent_complete = int((index + 1) / total_rows * 100)
                progress_bar.progress(percent_complete)
                status_text.text(f"🚀 Đang xử lý dòng {index + 1}/{total_rows}...")

            # Ép kiểu dữ liệu ngày tháng chuẩn hóa
            measurement_date = pd.to_datetime(row.get("measurement_date")).date().isoformat() if pd.notna(row.get("measurement_date")) else None
            cert_status = pd.to_datetime(row.get("cert_status")).date().isoformat() if pd.notna(row.get("cert_status")) else None
            invoice_date = pd.to_datetime(row.get("invoice_date")).date().isoformat() if pd.notna(row.get("invoice_date")) else None
            payment_status = str(row.get("payment_status")) if pd.notna(row.get("payment_status")) else None
            
            # Gán username mặc định nếu ô bị trống
            created_by = row.get("created_by") if pd.notna(row.get("created_by")) else st.session_state["username"]
            disable_notification = int(row.get("disable_calibration_notification", 0) or 0)
            disable_document_notification = int(row.get("disable_document_notification", 0) or 0)

            try:
                # 1. Đồng bộ Order
                DashboardService.sync_order(
                    customer_name=row.get("customer_name"),
                    order_number=row.get("order_number"),
                    measurement_date=measurement_date,
                    cert_status=cert_status,
                    sale_owner=row.get("sale_owner"),
                    created_by=created_by,
                    disable_calibration_notification=disable_notification,
                    disable_document_notification=disable_document_notification    
                )
                imported_orders += 1

                # 2. Đồng bộ Invoice
                total = float(row.get("total", 0) or 0)
                commission_percent = float(row.get("commission_percent", 0) or 0)
                payment_terms = row.get("payment_terms", 0)
                if pd.isna(payment_terms):
                    payment_terms = 0
                            
                PaymentService.save_invoice(
                    order_number=row.get("order_number"),
                    invoice_date=invoice_date,
                    invoice_group=row.get("invoice_group"),
                    payment_terms=payment_terms,
                    payment_status=payment_status,
                    total=total,
                    commission_percent=commission_percent,
                    note=row.get("note"),
                    invoice_created_by=created_by
                )
                imported_payments += 1
                
                # TỐI ƯU MẠNG: Nghỉ 0.01 giây để Database giải phóng bộ nhớ đệm kết nối, tránh đẩy traffic dồn dập
                time.sleep(0.01)

            except Exception as e:
                st.error(f"❌ Lỗi tại dòng {index + 2} (Mã đơn: {row.get('order_number')}): {str(e)}")
                continue

        # Hoàn tất dọn dẹp
        st.cache_data.clear()
        status_text.empty()
        progress_bar.empty()
        
        if "historical_df" in st.session_state:
            del st.session_state["historical_df"]
            
        st.success(f"🎉 Xuất sắc! Đã nạp thành công một mạch {imported_orders}/{total_rows} dòng vào ERP.")
        time.sleep(2)
        st.rerun()