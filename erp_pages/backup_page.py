import streamlit as st
from datetime import datetime

from utils.auth_guard import require_admin
from services.archive_service import ArchiveService
# Import hàm backup mới từ file pg_database của bạn
from languages import t
from database.pg_database import export_pg_backup 

def show_backup_page():
    require_admin()

    st.title(t("💾 Backup Database"))
    st.info(t("Generate and download current PostgreSQL database backup."))

    # 1. XỬ LÝ PHẦN BACKUP DATABASE (ĐÃ CHUYỂN SANG POSTGRES)
    with st.spinner(t("Preparing database backup...")):
        backup_data = export_pg_backup()

    if not backup_data:
        st.error(t("Could not generate database backup file. Please check server connection."))
    else:
        # Tên file backup bây giờ sẽ có đuôi là .sql thay vì .db
        backup_filename = f"app_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"

        st.download_button(
            label=t("📥 Download Backup (.sql)"),
            data=backup_data,
            file_name=backup_filename,
            mime="text/plain" # Định dạng file text SQL
        )
        st.success(t("Database backup is ready for download."))

    st.divider()

    # 2. PHẦN FULL ERP ARCHIVE EXCEL (GIỮ NGUYÊN)
    st.subheader(t("📊 Full ERP Archive"))
    
    archive_data = ArchiveService.export_full_archive()
    archive_filename = f"ERP_Archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    st.download_button(
        label=t("📥 Export Full Excel Archive"),
        data=archive_data,
        file_name=archive_filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.divider()

    # 3. PHẦN THỐNG KÊ STATISTICS (TỰ ĐỘNG CHẠY THEO POSTGRES)
    st.subheader(t("📈 Database Statistics"))

    # Lưu ý: Các file Repositories (OrderRepository, PaymentRepository...) 
    # sau này khi bạn sửa sang dùng PostgreSQL, thì các hàm count dưới đây 
    # tự động trả về số liệu của Postgres mà không cần sửa một chữ nào ở trang này cả!
    from repositories.order_repository import OrderRepository
    from repositories.payment_repository import PaymentRepository
    from repositories.document_tracking_repository import DocumentTrackingRepository
    from repositories.log_repository import LogRepository

    orders_count = len(OrderRepository.get_all_orders())
    payments_count = len(PaymentRepository.get_all_payments())
    tracking_count = len(DocumentTrackingRepository.get_all())
    logs_count = LogRepository.get_log_count()

    col1, col2 = st.columns(2)
    with col1:
        st.metric(t("Orders"), orders_count)
        st.metric(t("Payments"), payments_count)

    with col2:
        st.metric(t("Tracking"), tracking_count)
        st.metric(t("Logs"), logs_count)