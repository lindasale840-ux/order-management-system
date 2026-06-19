import streamlit as st
import pandas as pd

from services.finance_service import (
    FinanceService
)
from repositories.order_repository import (
    OrderRepository
)
from repositories.document_tracking_repository import (
    DocumentTrackingRepository
)
from components.aggrid_table import (
    render_aggrid
)
from utils.excel_export import (
    dataframe_to_excel
)
from config.app_config import DOCUMENT_WARNING_DAYS


def export_button(df, filename):
    excel_data = dataframe_to_excel({"Data": df})
    st.download_button(
        label="📥 Export Excel",
        data=excel_data,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def show_notification_page():
    st.title("🔔 Notification Center")

    # ========================================================
    # ĐÃ NÂNG CẤP: Thanh tìm kiếm tự do toàn diện (Global Search Text Input)
    # ========================================================
    search_keyword = st.text_input("🔍 Fast Query Search Client Account / Target Order Sequence").strip()

    df = FinanceService.build_finance_dataframe()

    # Nếu người dùng có nhập từ khóa, tiến hành lọc trên toàn bộ các cột liên quan
    if search_keyword:
        # Tạo điều kiện lọc không phân biệt chữ hoa chữ thường (case-insensitive)
        customer_match = df["customer_name"].astype(str).str.contains(search_keyword, case=False, na=False)
        
        # Phòng trường hợp df gốc có cột order_number để tìm kiếm theo mã đơn
        if "order_number" in df.columns:
            order_match = df["order_number"].astype(str).str.contains(search_keyword, case=False, na=False)
            df = df[customer_match | order_match]
        else:
            df = df[customer_match]

    missing_cert_df = df[df["cert_workflow_status"] == "Missing Cert"]

    # Thêm điều kiện loại trừ các đơn hàng có disable_payment_notification == 1
    payment_overdue_df = df[
        (df["payment_overdue"] == "Overdue")
        & (df["disable_payment_notification"] != 1)
    ]

    due_soon_df = df[
        (df["cert_due_soon"] == "Due Soon")
        & (df["disable_calibration_notification"] != 1)
    ]
    
    calibration_overdue_df = df[
        (df["cert_overdue"] == "Overdue")
        & (df["disable_calibration_notification"] != 1)
    ]

    missing_invoice_df = df[df["order_status"] == "Missing Invoice"]

    today = pd.Timestamp.today()

    # =========================
    # MISSING DOCUMENT SENDING
    # =========================
    tracking_df = DocumentTrackingRepository.get_latest_tracking()
    sent_orders = set()

    if not tracking_df.empty:
        sent_orders = set(tracking_df["order_number"].astype(str))

    missing_document_df = df.copy()
    missing_document_df["cert_status"] = pd.to_datetime(
        missing_document_df["cert_status"],
        errors="coerce"
    )

    missing_document_df = missing_document_df[
        missing_document_df["cert_status"].notna()
        & (today - missing_document_df["cert_status"]).dt.days.gt(DOCUMENT_WARNING_DAYS)
        & (~missing_document_df["order_number"].astype(str).isin(sent_orders))
        & (missing_document_df["disable_document_notification"] != 1)
    ]

    pending_return_df = tracking_df.copy()
    ignore_orders = set(df[df["disable_document_notification"] == 1]["order_number"])

    if not pending_return_df.empty:
        pending_return_df["sent_date"] = pd.to_datetime(
            pending_return_df["sent_date"],
            errors="coerce"
        )
        pending_return_df["received_date"] = pd.to_datetime(
            pending_return_df["received_date"],
            errors="coerce"
        )

        pending_return_df = pending_return_df[
            pending_return_df["received_date"].isna()
            & (today - pending_return_df["sent_date"]).dt.days.gt(DOCUMENT_WARNING_DAYS)
        ]

        if not pending_return_df.empty:
            pending_return_df["sent_date"] = pd.to_datetime(
                pending_return_df["sent_date"],
                errors="coerce"
            )
            pending_return_df = pending_return_df[
                (today - pending_return_df["sent_date"]).dt.days.gt(DOCUMENT_WARNING_DAYS)
            ]
            pending_return_df = pending_return_df[
                ~pending_return_df["order_number"].isin(ignore_orders)
            ]

            # Đồng bộ bộ lọc tìm kiếm text cho cả dữ liệu phụ Pending Return (Lọc theo mã đơn hoặc tên khách hàng)
            if search_keyword:
                pending_customer_match = pending_return_df["customer_name"].astype(str).str.contains(search_keyword, case=False, na=False)
                pending_order_match = pending_return_df["order_number"].astype(str).str.contains(search_keyword, case=False, na=False)
                pending_return_df = pending_return_df[pending_customer_match | pending_order_match]

    # =========================
    # KPI SUMMARY
    # =========================
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

    with col1:
        st.metric("📄 Missing Cert", len(missing_cert_df))
    with col2:
        st.metric("💰 Payment Overdue", len(payment_overdue_df))
    with col3:
        st.metric("📅 Due Soon", len(due_soon_df))
    with col4:
        st.metric("🧾 Missing Invoice", len(missing_invoice_df))
    with col5:
        st.metric("📨 Missing Send", len(missing_document_df))
    with col6:
        st.metric("📬 Pending Return", len(pending_return_df))  
    with col7:
        st.metric("⛔ Calibration Overdue", len(calibration_overdue_df))      

    st.divider()

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        f"📄 Missing Cert ({len(missing_cert_df)})",
        f"💰 Payment Overdue ({len(payment_overdue_df)})",
        f"📅 Due Soon ({len(due_soon_df)})",
        f"🧾 Missing Invoice ({len(missing_invoice_df)})",
        f"📨 Missing Send ({len(missing_document_df)})",
        f"📬 Pending Return ({len(pending_return_df)})",
        f"⛔ Calibration Overdue ({len(calibration_overdue_df)})"
    ])

    # =========================
    # TAB 1
    # =========================
    with tab1:
        st.metric("Missing Certificate", len(missing_cert_df))
        if missing_cert_df.empty:
            st.success("No missing certificate matching parameters")
        else:
            render_aggrid(
                missing_cert_df,
                height=500,
                page_size=10,
                key="missing_cert_grid"
            )
            export_button(missing_cert_df, "missing_certificate.xlsx")

    # =========================
    # TAB 2
    # =========================
    with tab2:
        st.metric("Payment Overdue", len(payment_overdue_df))
        if payment_overdue_df.empty:
            st.success("No overdue payment matching parameters")
        else:
            render_aggrid(
                payment_overdue_df,
                height=500,
                page_size=10,
                key="payment_overdue_grid"
            )
            export_button(payment_overdue_df, "payment_overdue.xlsx")

    # =========================
    # TAB 3
    # =========================
    with tab3:
        st.metric("Calibration Due Soon", len(due_soon_df))
        if due_soon_df.empty:
            st.success("No due soon matching parameters")
        else:
            render_aggrid(
                due_soon_df,
                height=500,
                page_size=10,
                key="due_soon_grid"
            )
            export_button(due_soon_df, "calibration_due_soon.xlsx")

    # =========================
    # TAB 4
    # =========================
    with tab4:
        st.metric("Missing Invoice", len(missing_invoice_df))
        if missing_invoice_df.empty:
            st.success("No missing invoice matching parameters")
        else:
            render_aggrid(
                missing_invoice_df,
                height=500,
                page_size=10,
                key="missing_invoice_grid"
            )
            export_button(missing_invoice_df, "missing_invoice.xlsx")

    # =========================
    # TAB 5
    # =========================
    with tab5:
        st.metric("Missing Document Sending", len(missing_document_df))
        if missing_document_df.empty:
            st.success("No missing document sending matching parameters")
        else:
            render_aggrid(
                missing_document_df,
                height=500,
                page_size=10,
                key="missing_document_grid"
            )
            export_button(missing_document_df, "missing_document_sending.xlsx")

    # =========================
    # TAB 6
    # =========================
    with tab6:
        st.metric("Pending Return", len(pending_return_df))
        if pending_return_df.empty:
            st.success("No pending return matching parameters")
        else:
            display_df = pending_return_df[["customer_name", "order_number", "sent_date", "note"]].copy()
            render_aggrid(
                display_df,
                height=500,
                page_size=10,
                key="pending_return_grid"
            )
            export_button(display_df, "pending_return.xlsx")
            
    # =========================
    # TAB 7
    # =========================
    with tab7:
        st.metric("Calibration Overdue", len(calibration_overdue_df))
        if calibration_overdue_df.empty:
            st.success("No overdue calibration matching parameters")
        else:
            render_aggrid(
                calibration_overdue_df,
                height=500,
                page_size=10,
                key="calibration_overdue_grid"
            )
            export_button(calibration_overdue_df, "calibration_overdue.xlsx")