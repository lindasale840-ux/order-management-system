import streamlit as st
import pandas as pd
from datetime import date
from repositories.order_repository import OrderRepository
from repositories.payment_repository import PaymentRepository
from services.payment_service import PaymentService
from utils.data_permission import filter_by_sale_owner
from utils.auth_guard import require_editor
# Chỉ cần import đúng 1 dòng này từ file languages
from languages import t

def show_payment_page():
    require_editor()

    st.title(t("payment_invoice_ledger_managem"))
    
    if st.session_state.get("invoice_saved"):
        st.success(t("invoice_details_safely_committ"))
        st.session_state["invoice_saved"] = False

    order_df = OrderRepository.get_all_orders()
    order_df = filter_by_sale_owner(order_df)

    # Global search box
    search_keyword = st.text_input(t("fast_query_search_client_accou")).strip()
    
    if search_keyword:
        order_df = order_df[
            order_df["customer_name"].astype(str).str.contains(search_keyword, case=False, na=False) |
            order_df["order_number"].astype(str).str.contains(search_keyword, case=False, na=False)
        ]

    order_list = order_df["order_number"].tolist()

    if not order_list:
        st.warning(t("no_available_core_order_entrie"))
        return

    if order_df.empty:
        st.warning(t("query_mismatch_no_records_matc"))
        return
    
    selected_order = st.selectbox(t("select_order_number_pipeline"), order_list)

    payment_df = PaymentRepository.get_all_payments()
    existing = payment_df[payment_df["order_number"] == selected_order]
    existing_data = {}

    if not existing.empty:
        existing_data = existing.iloc[0].to_dict()

    invoice_group = st.text_input(
        t("invoice_group_code"),
        value=str(existing_data.get("invoice_group", "") or "")
    )
    
    # Load past parameters or generate fresh date stamp
    invoice_date_value = date.today()
    invoice_date_raw = existing_data.get("invoice_date")
    if pd.notna(invoice_date_raw):
        invoice_date_value = pd.to_datetime(invoice_date_raw).date()

    payment_status_saved = existing_data.get("payment_status")
    if pd.isna(payment_status_saved):
        unpaid_default = True
        payment_status_value = date.today()
    else:
        unpaid_default = False
        payment_status_value = pd.to_datetime(payment_status_saved).date()

    col1, col2 = st.columns(2)

    with col1:
        invoice_date = st.date_input(t("invoice_distribution_date"), value=invoice_date_value)
        payment_terms = st.number_input(
            t("payment_terms_30_365_days_cred"),
            min_value=30,   # Chặn cứng không cho bấm nút giảm xuống dưới 30
            max_value=365,  # Chặn cứng không cho bấm nút tăng quá 365
            value=max(30, min(int(existing_data.get("payment_terms", 30) or 30), 365)), # Ép giá trị mặc định luôn nằm trong khoảng [30, 365]
            step=1
        )
        total = st.number_input(
            t("total_invoice_valuation_amount"),
            min_value=0.0,
            value=float(existing_data.get("total", 0) or 0)
        )

    with col2:
        unpaid = st.checkbox(t("mark_as_unpaid_outstanding_deb"), value=unpaid_default)

        if unpaid:
            payment_status = None
            st.info(t("system_flags_this_invoice_reco"))
        else:
            payment_status = st.date_input(t("actual_settled_date_target"), value=payment_status_value)

        commission_percent = st.number_input(
            t("commission_ratio"),
            min_value=0.0,
            value=float(existing_data.get("commission_percent", 0) or 0)
        )
        note = st.text_area(t("operational_ledger_remarks_not"), value=str(existing_data.get("note", "") or ""))

    # Calculation Output UI Card
    commission_actual = total * commission_percent / 100
    st.metric(t("calculated_net_commission_yiel"), f"${commission_actual:,.2f}")

    # --- VALIDATION ĐIỀU KIỆN LƯU HÓA ĐƠN ---
    # --- VALIDATION ĐIỀU KIỆN LƯU HÓA ĐƠN ---
    # Nút bấm sẽ bị khóa nếu: Trống nhóm hóa đơn HOẶC số tiền <= 0 HOẶC số ngày nằm ngoài khoảng 30-365
    is_invoice_invalid = (
        (not invoice_group.strip()) or 
        (total <= 0.0) or 
        (payment_terms < 30) or 
        (payment_terms > 365)
    )

    if is_invoice_invalid:
        st.warning(t("fields_marked_required_payment"))
    if st.button(t("save_invoice_changes"), use_container_width=True, disabled=is_invoice_invalid):
        PaymentService.save_invoice(
            selected_order,
            invoice_date,
            invoice_group,
            payment_terms,
            payment_status,
            total,
            commission_percent,
            note
        )
        st.session_state["invoice_saved"] = True
        st.rerun()