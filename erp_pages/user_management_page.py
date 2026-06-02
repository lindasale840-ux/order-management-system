import streamlit as st

from repositories.user_repository import (
    UserRepository
)

from utils.password_utils import (
    hash_password
)

from utils.auth_guard import (
    require_admin
)

def show_user_management_page():

    require_admin()
    
    st.title(
        "👥 User Management"
    )

    st.subheader(
        "Create User"
    )

    username = st.text_input(
        "Username"
    )

    password = st.text_input(
        "Password",
        type="password"
    )

    role = st.selectbox(

        "Role",

        [

            "USER",

            "MANAGER",

            "ADMIN"
        ]
    )

    if st.button(
        "Create User"
    ):

        if not username:

            st.error(
                "Username required"
            )

        elif not password:

            st.error(
                "Password required"
            )

        else:

            existing = (

                UserRepository
                .get_user_by_username(
                    username
                )
            )

            if existing:

                st.error(
                    "User already exists"
                )

            else:

                UserRepository.create_user(

                    username,

                    hash_password(
                        password
                    ),

                    role
                )

                st.success(
                    "User created"
                )

    st.divider()

    st.subheader(
        "Existing Users"
    )

    users_df = (
        UserRepository
        .get_all_users()
    )

    st.dataframe(

        users_df,

        width="stretch"
    )

    st.divider()

    st.subheader(
        "Delete User"
    )

    user_list = users_df[
        "username"
    ].tolist()

    if user_list:

        delete_user = st.selectbox(

            "Select User",

            user_list
        )

        if st.button(
            "Delete User"
        ):

            if delete_user == "admin":

                st.error(
                    "Cannot delete admin"
                )

            else:

                UserRepository.delete_user(
                    delete_user
                )

                st.success(
                    "User deleted"
                )

                st.rerun()