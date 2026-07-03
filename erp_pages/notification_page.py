import streamlit as st
import pandas as pd

from services.finance_service import FinanceService
from repositories.order_repository import OrderRepository
from repositories.document_tracking_repository import DocumentTrackingRepository
from components.aggrid_table import render_aggrid
from utils.excel_export import dataframe_to_excel
from config.app_config import DOCUMENT_WARNING_DAYS
# Chỉ cần import đúng 1 dòng này từ file languages
from languages import t

def export_button(df, filename):
    excel_data = dataframe_to_excel({"Data": df})
    st.download_button(
        label="📥 Export Excel",
        data=excel_data,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def show_notification_page():
    st.title(t("notification_center"))

    # ========================================================
    # GLOBAL SEARCH FILTER
    # ========================================================
    search_keyword = st.text_input(t("fast_query_search_client_accou")).strip()

    df = FinanceService.build_finance_dataframe()

    if search_keyword:
        customer_match = df["customer_name"].astype(str).str.contains(search_keyword, case=False, na=False)
        if "order_number" in df.columns:
            order_match = df["order_number"].astype(str).str.contains(search_keyword, case=False, na=False)
            df = df[customer_match | order_match]
        else:
            df = df[customer_match]

    missing_cert_df = df[df["cert_workflow_status"] == "Missing Cert"]

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
    # MISSING DOCUMENT SENDING LOGIC
    # =========================
    tracking_df = DocumentTrackingRepository.get_latest_tracking()
    df = FinanceService.build_finance_dataframe()

    allowed_orders = set(
        df["order_number"].astype(str)
    )

    tracking_df = tracking_df[
        tracking_df["order_number"].astype(str)
        .isin(allowed_orders)
    ]
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

            if search_keyword:
                pending_customer_match = pending_return_df["customer_name"].astype(str).str.contains(search_keyword, case=False, na=False)
                pending_order_match = pending_return_df["order_number"].astype(str).str.contains(search_keyword, case=False, na=False)
                pending_return_df = pending_return_df[pending_customer_match | pending_order_match]

    # =========================
    # KPI SUMMARY
    # =========================
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

    with col1:
        st.metric(t('tab_missing_cert'), len(missing_cert_df))
    with col2:
        st.metric(t('tab_payment_overdue'), len(payment_overdue_df))
    with col3:
        st.metric(t('tab_due_soon'), len(due_soon_df))
    with col4:
        st.metric(t('tab_missing_invoice'), len(missing_invoice_df))
    with col5:
        st.metric(t('tab_missing_send'), len(missing_document_df))
    with col6:
        st.metric(t('tab_pending_return'), len(pending_return_df))  
    with col7:
        st.metric(t('tab_calibration_overdue'), len(calibration_overdue_df))      

    st.divider()

    # ========================================================
    # ĐỘT PHÁ: BỘ ĐIỀU KHIỂN PHÂN TRANG DÙNG CHUNG CHO TẤT CẢ CÁC TABS
    # ========================================================
    st.subheader(t("filtered_alert_logs_controller"))
    col_p1, col_p2, col_p3 = st.columns([2, 2, 6])
    with col_p1:
        rows_per_page = st.selectbox(
            "Rows per page",
            options=[5, 10, 20, 50, 100],
            index=1,
            key="notify_global_rows_per_page"
        )
    
    # Tìm tập dữ liệu lớn nhất hiện tại trong 7 tabs để tính số trang an toàn nhất
    max_current_rows = max(
        len(missing_cert_df), len(payment_overdue_df), len(due_soon_df),
        len(missing_invoice_df), len(missing_document_df), len(pending_return_df),
        len(calibration_overdue_df), 1
    )
    total_pages = max(1, (max_current_rows + rows_per_page - 1) // rows_per_page)
    
    with col_p2:
        selected_page = st.selectbox(
            "Go to page",
            options=list(range(1, total_pages + 1)),
            index=0,
            key="notify_global_page_select"
        )
        
    # Tính chỉ số Index cắt lát dữ liệu
    start_idx = (selected_page - 1) * rows_per_page
    end_idx = start_idx + rows_per_page

    # ========================================================
    # RENDER TABS SYSTEM
    # ========================================================
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    f"{t('tab_missing_cert')} ({len(missing_cert_df)})",
    f"{t('tab_payment_overdue')} ({len(payment_overdue_df)})",
    f"{t('tab_due_soon')} ({len(due_soon_df)})",
    f"{t('tab_missing_invoice')} ({len(missing_invoice_df)})",
    f"{t('tab_missing_send')} ({len(missing_document_df)})",
    f"{t('tab_pending_return')} ({len(pending_return_df)})",
    f"{t('tab_calibration_overdue')} ({len(calibration_overdue_df)})"
])

    # --- TAB 1 ---
    with tab1:
        st.metric(t("lbl_missing_cert"), len(missing_cert_df))
        if missing_cert_df.empty:
            st.success(t("msg_no_missing_cert"))
        else:
            sliced_cert_df = missing_cert_df.iloc[start_idx:end_idx]
            render_aggrid(sliced_cert_df, height=500, page_size=rows_per_page, pagination=False, key="missing_cert_grid")
            export_button(missing_cert_df, "missing_certificate.xlsx")

    # --- TAB 2 ---
    with tab2:
        st.metric(t("payment_overdue"), len(payment_overdue_df))
        if payment_overdue_df.empty:
            st.success(t("no_overdue_payment_matching_pa"))
        else:
            sliced_payment_df = payment_overdue_df.iloc[start_idx:end_idx]
            render_aggrid(sliced_payment_df, height=500, page_size=rows_per_page, pagination=False, key="payment_overdue_grid")
            export_button(payment_overdue_df, "payment_overdue.xlsx")

    # --- TAB 3 ---
    with tab3:
        st.metric(t("calibration_due_soon"), len(due_soon_df))
        if due_soon_df.empty:
            st.success(t("no_due_soon_matching_parameter"))
        else:
            sliced_due_df = due_soon_df.iloc[start_idx:end_idx]
            render_aggrid(sliced_due_df, height=500, page_size=rows_per_page, pagination=False, key="due_soon_grid")
            export_button(due_soon_df, "calibration_due_soon.xlsx")

    # --- TAB 4 ---
    with tab4:
        st.metric(t("missing_invoice"), len(missing_invoice_df))
        if missing_invoice_df.empty:
            st.success(t("no_missing_invoice_matching_pa"))
        else:
            sliced_invoice_df = missing_invoice_df.iloc[start_idx:end_idx]
            render_aggrid(sliced_invoice_df, height=500, page_size=rows_per_page, pagination=False, key="missing_invoice_grid")
            export_button(missing_invoice_df, "missing_invoice.xlsx")

    # --- TAB 5 ---
    with tab5:
        st.metric(t("missing_document_sending"), len(missing_document_df))
        if missing_document_df.empty:
            st.success(t("no_missing_document_sending_ma"))
        else:
            sliced_doc_df = missing_document_df.iloc[start_idx:end_idx]
            render_aggrid(sliced_doc_df, height=500, page_size=rows_per_page, pagination=False, key="missing_document_grid")
            export_button(missing_document_df, "missing_document_sending.xlsx")

    # --- TAB 6 ---
    with tab6:
        st.metric(t("pending_return"), len(pending_return_df))
        if pending_return_df.empty:
            st.success(t("no_pending_return_matching_par"))
        else:
            display_df = pending_return_df[["customer_name", "order_number", "sent_date", "note"]].copy()
            sliced_return_df = display_df.iloc[start_idx:end_idx]
            render_aggrid(sliced_return_df, height=500, page_size=rows_per_page, pagination=False, key="pending_return_grid")
            export_button(display_df, "pending_return.xlsx")
            
    # --- TAB 7 ---
    with tab7:
        st.metric(t("calibration_overdue"), len(calibration_overdue_df))
        if calibration_overdue_df.empty:
            st.success(t("no_overdue_calibration_matchin"))
        else:
            sliced_calib_df = calibration_overdue_df.iloc[start_idx:end_idx]
            render_aggrid(sliced_calib_df, height=500, page_size=rows_per_page, pagination=False, key="calibration_overdue_grid")
            export_button(calibration_overdue_df, "calibration_overdue.xlsx")