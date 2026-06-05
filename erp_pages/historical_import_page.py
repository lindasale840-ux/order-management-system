import streamlit as st
import pandas as pd

from utils.auth_guard import (
    require_admin
)


def show_historical_import_page():

    require_admin()

    st.title(
        "📥 Historical Data Import"
    )

    uploaded_file = st.file_uploader(

        "Upload Historical Excel",

        type=["xlsx"]
    )

    if uploaded_file is None:

        st.info(
            "Please upload Excel file."
        )

        return

    df = pd.read_excel(
        uploaded_file
    )

    st.success(
        f"{len(df)} rows loaded"
    )

    st.dataframe(
        df,
        use_container_width=True
    )