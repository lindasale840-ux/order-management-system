import streamlit as st

from repositories.log_repository import (
    LogRepository
)

from components.aggrid_table import (
    render_aggrid
)

from utils.excel_export import (
    dataframe_to_excel
)

def show_logs_page():

    st.title("Logs")

    page_size = st.selectbox(

        "Rows per page",

        [5, 10, 20, 50],

        index=0,

        key="logs_page_size"
    )

    df = LogRepository.get_logs()

    render_aggrid(

        df,

        height=500,

        page_size=page_size
    )


    excel_data = dataframe_to_excel({

    "Logs": df
    })

    st.download_button(

        label="📥 Export Logs Excel",

        data=excel_data,

        file_name="system_logs.xlsx",

        mime=(
            "application/vnd.openxmlformats-"
            "officedocument.spreadsheetml.sheet"
        )
    )