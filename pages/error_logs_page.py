import streamlit as st

from repositories.error_log_repository import (
    ErrorLogRepository
)

from components.aggrid_table import (
    render_aggrid
)

from utils.auth_guard import (
    require_admin
)


def show_error_logs_page():

    require_admin()
    
    st.title(
        "🚨 Error Logs"
    )

    df = (
        ErrorLogRepository
        .get_errors()
    )

    if df.empty:

        st.success(
            "No errors found"
        )

        return

    render_aggrid(

        df,

        height=500,

        page_size=10
    )