import streamlit as st

from services.auth_service import (
    AuthService
)


def show_login_page():

    st.markdown("# 🔐 Login")

    with st.form("login_form"):

        username = st.text_input(
            "Username"
        )

        password = st.text_input(
            "Password",
            type="password"
        )

        login_btn = st.form_submit_button(
            "Login"
        )

    if login_btn:

        user = AuthService.login(

            username,

            password
        )

        if not user:

            st.error(
                "Invalid username or password"
            )

            return

        st.session_state[
            "logged_in"
        ] = True

        st.session_state[
            "username"
        ] = user["username"]

        st.session_state[
            "role"
        ] = user["role"]

        st.rerun()