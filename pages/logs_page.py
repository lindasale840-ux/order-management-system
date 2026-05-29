import streamlit as st

from repositories.log_repository import (
    LogRepository
)

from components.pagination import (
    paginate_dataframe
)


def show_logs_page():

    st.title("Logs")

    df = LogRepository.get_logs()

    paginated_df = paginate_dataframe(

        df,

        "logs",

        5
    )

    st.dataframe(

        paginated_df,

        use_container_width=True
    )