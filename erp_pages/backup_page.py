import streamlit as st
from pathlib import Path
from datetime import datetime

from utils.auth_guard import (
    require_admin
)

from services.archive_service import (
    ArchiveService
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

    st.divider()

    st.subheader(
        "📊 Full ERP Archive"
    )

    archive_data = (
        ArchiveService.export_full_archive()
    )

    archive_filename = (

        "ERP_Archive_"

        +

        datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        +

        ".xlsx"
    )

    st.download_button(

        label="📥 Export Full Excel Archive",

        data=archive_data,

        file_name=archive_filename,

        mime=(
            "application/vnd.openxmlformats-"
            "officedocument.spreadsheetml.sheet"
        )
    )

    st.divider()

    st.subheader(
        "📈 Database Statistics"
    )

    from repositories.order_repository import (
    OrderRepository
    )

    from repositories.payment_repository import (
        PaymentRepository
    )

    from repositories.document_tracking_repository import (
        DocumentTrackingRepository
    )

    from repositories.log_repository import (
        LogRepository
    )

    orders_count = len(
    OrderRepository.get_all_orders()
    )

    payments_count = len(
        PaymentRepository.get_all_payments()
    )

    tracking_count = len(
        DocumentTrackingRepository.get_all()
    )

    logs_count = (
        LogRepository.get_log_count()
    )

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Orders",
            orders_count
        )

        st.metric(
            "Payments",
            payments_count
        )

    with col2:

        st.metric(
            "Tracking",
            tracking_count
        )

        st.metric(
            "Logs",
            logs_count
        )