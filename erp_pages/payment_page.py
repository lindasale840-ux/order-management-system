import streamlit as st
import pandas as pd
from datetime import date
from repositories.order_repository import OrderRepository
from repositories.payment_repository import PaymentRepository
from services.payment_service import PaymentService
from utils.data_permission import filter_by_sale_owner
from utils.auth_guard import require_editor

def show_payment_page():
    require_editor()

    st.title("💰 Payment & Invoice Ledger Management")
    
    if st.session_state.get("invoice_saved"):
        st.success("🎉 Invoice details safely committed to master branch.")
        st.session_state["invoice_saved"] = False

    order_df = OrderRepository.get_all_orders()
    order_df = filter_by_sale_owner(order_df)

    # Global search box
    search_keyword = st.text_input("🔍 Fast Query Search Client Account / Target Order Sequence").strip()
    
    if search_keyword:
        order_df = order_df[
            order_df["customer_name"].astype(str).str.contains(search_keyword, case=False, na=False) |
            order_df["order_number"].astype(str).str.contains(search_keyword, case=False, na=False)
        ]

    order_list = order_df["order_number"].tolist()

    if not order_list:
        st.warning("⚠️ No available core order entries detected under current parameters.")
        return

    if order_df.empty:
        st.warning("⚠️ Query mismatch: No records matching keywords.")
        return
    
    selected_order = st.selectbox("Select Order Number Pipeline", order_list)

    payment_df = PaymentRepository.get_all_payments()
    existing = payment_df[payment_df["order_number"] == selected_order]
    existing_data = {}

    if not existing.empty:
        existing_data = existing.iloc[0].to_dict()

    invoice_group = st.text_input(
        "Invoice Group Code (*)",
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
        invoice_date = st.date_input("Invoice Distribution Date", value=invoice_date_value)
        payment_terms = st.number_input(
            "Payment Terms (30 - 365 Days Credit) (*)",
            min_value=30,   # Chặn cứng không cho bấm nút giảm xuống dưới 30
            max_value=365,  # Chặn cứng không cho bấm nút tăng quá 365
            value=max(30, min(int(existing_data.get("payment_terms", 30) or 30), 365)), # Ép giá trị mặc định luôn nằm trong khoảng [30, 365]
            step=1
        )
        total = st.number_input(
            "Total Invoice Valuation Amount (*)",
            min_value=0.0,
            value=float(existing_data.get("total", 0) or 0)
        )

    with col2:
        unpaid = st.checkbox("Mark as Unpaid / Outstanding Debt", value=unpaid_default)

        if unpaid:
            payment_status = None
            st.info("ℹ️ System flags this invoice record balance as pending payment.")
        else:
            payment_status = st.date_input("Actual Settled Date Target", value=payment_status_value)

        commission_percent = st.number_input(
            "Commission Ratio (%)",
            min_value=0.0,
            value=float(existing_data.get("commission_percent", 0) or 0)
        )
        note = st.text_area("Operational Ledger Remarks & Notes", value=str(existing_data.get("note", "") or ""))

    # Calculation Output UI Card
    commission_actual = total * commission_percent / 100
    st.metric("Calculated Net Commission Yield", f"${commission_actual:,.2f}")

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
        st.warning("⚠️ Fields marked (*) require valid entries to authorize save execution. (Invoice Group non-empty, Total valuation > 0, Payment Terms must be between 30 and 365 days).")
    if st.button("💾 Save Invoice Changes", use_container_width=True, disabled=is_invoice_invalid):
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