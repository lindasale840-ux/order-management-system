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

            if confirm:

                OwnershipTransferService.transfer_assistant(

                    old_assistant,

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

            if confirm2:

                OwnershipTransferService.transfer_sale(

                    old_sale,

                    new_sale

                )

                st.success(
                    "Transfer completed"
                )

                st.rerun()