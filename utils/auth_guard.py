import streamlit as st


def require_admin():

    if st.session_state.get("role") != "ADMIN":

        st.error(
            "Admin only page"
        )

        st.stop()

def require_manager():

    if st.session_state.get(
        "role"
    ) not in [

        "ADMIN",

        "MANAGER"

    ]:

        st.error(
            "Manager only page"
        )

        st.stop()

def require_login():

    if not st.session_state.get(

        "logged_in",

        False

    ):

        st.error(
            "Please login"
        )

        st.stop()

def require_editor():

    if st.session_state.get(
        "role"
    ) not in [

        "ADMIN",

        "ASSISTANT"

    ]:

        st.error(
            "No permission"
        )

        st.stop()        