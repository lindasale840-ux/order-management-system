import streamlit as st

from utils.auth_guard import (
    require_admin
)

from repositories.user_repository import (
    UserRepository
)

from services.ownership_transfer_service import (
    OwnershipTransferService
)

from repositories.payment_repository import PaymentRepository
from repositories.order_repository import OrderRepository


def show_ownership_transfer_page():

    require_admin()

    st.title(
        "🔄 Ownership Transfer"
    )

    users_df = (
        UserRepository.get_all_users()
    )

    assistant_users = users_df[
        users_df["role"] == "ASSISTANT"
    ]["username"].tolist()

    sale_users = users_df[
        users_df["role"] == "SALE"
    ]["sale_owner"].dropna().unique().tolist()

    tab1, tab2 = st.tabs([
        "Assistant Transfer",
        "Sale Transfer"
    ])

    with tab1:

        st.subheader(
            "Transfer Assistant Revenue"
        )

        old_assistant = st.selectbox(

            "From Assistant",

            assistant_users

        )
        
        payments_df = PaymentRepository.get_all_payments()

        assistant_orders = payments_df[
            payments_df["invoice_created_by"] == old_assistant
        ]["order_number"].tolist()

        selected_orders = st.multiselect(
            "Select Orders",
            assistant_orders
        )

        new_assistant = st.selectbox(

            "To Assistant",

            assistant_users,

            key="assistant_target"

        )

        confirm = st.checkbox(

            "Confirm Assistant Transfer"

        )

        if st.button(
            "Transfer Assistant"
        ):

            if not selected_orders:

                st.error(
                    "Please select at least one order"
                )

            elif not confirm:

                st.error(
                    "Please confirm first"
                )

            else:

                OwnershipTransferService.transfer_assistant_orders(

                    selected_orders,

                    new_assistant

                )

                st.success(
                    "Transfer completed"
                )

                st.rerun()

    with tab2:

        st.subheader(
            "Transfer Sale Owner"
        )

        old_sale = st.selectbox(

            "From Sale",

            sale_users

        )
        
        orders_df = OrderRepository.get_all_orders()

        sale_orders = orders_df[
            orders_df["sale_owner"] == old_sale
        ]["order_number"].tolist()

        selected_sale_orders = st.multiselect(
            "Select Orders",
            sale_orders,
            key="sale_order_select"
        )

        new_sale = st.selectbox(

            "To Sale",

            sale_users,

            key="sale_target"

        )

        confirm2 = st.checkbox(

            "Confirm Sale Transfer"

        )

        if st.button(
            "Transfer Sale"
        ):

            if not selected_sale_orders:

                st.error(
                    "Please select at least one order"
                )

            elif not confirm2:

                st.error(
                    "Please confirm first"
                )

            else:

                OwnershipTransferService.transfer_sale_orders(

                    selected_sale_orders,

                    new_sale

                )

                st.success(
                    "Transfer completed"
                )

                st.rerun()