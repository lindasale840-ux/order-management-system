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

from utils.excel_export import (
    dataframe_to_excel
)


def show_error_logs_page():

    require_admin()

    st.title(
        "🚨 Error Logs"
    )

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "🗑 Delete All Error Logs"
        ):

            ErrorLogRepository.delete_all_errors()

            st.success(
                "All error logs deleted"
            )

            st.rerun()

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

    st.divider()

    excel_data = dataframe_to_excel({

        "Error Logs": df

    })

    st.download_button(

        label="📥 Export Error Logs Excel",

        data=excel_data,

        file_name="error_logs.xlsx",

        mime=(
            "application/vnd.openxmlformats-"
            "officedocument.spreadsheetml.sheet"
        )
    )