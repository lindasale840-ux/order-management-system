import streamlit as st
from pathlib import Path
from datetime import datetime

from utils.auth_guard import (
    require_admin
)


def show_backup_page():

    require_admin()

    st.title(
        "💾 Backup Database"
    )

    st.info(
        "Download current SQLite database."
    )

    db_path = Path(
        "database/app.db"
    )

    if not db_path.exists():

        st.error(
            "Database file not found."
        )

        return

    backup_filename = (

        "app_backup_"

        +

        datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        +

        ".db"
    )

    with open(
        db_path,
        "rb"
    ) as file:

        st.download_button(

            label="📥 Download Backup",

            data=file,

            file_name=backup_filename,

            mime=(
                "application/octet-stream"
            )
        )

    st.success(
        "Database ready for download."
    )