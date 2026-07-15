from repositories.order_repository import OrderRepository
from repositories.log_repository import LogRepository
import streamlit as st

class DashboardService:

    @staticmethod
    def sync_order(
        customer_name,
        order_number,
        measurement_date,
        cert_status,
        sale_owner,
        created_by,
        disable_calibration_notification=0,
        disable_document_notification=0,
        disable_payment_notification=0,  # Tham số mới bổ sung trước đó
        cert_warning_days=None,          # <-- Bổ sung tham số cấu hình động mới (an toàn 100%)
        doc_warning_days=None            # <-- Bổ sung tham số cấu hình động mới (an toàn 100%)
    ):
        # Truyền đầy đủ các tham số cấu hình mới xuống OrderRepository
        OrderRepository.upsert_order(
            customer_name=customer_name,
            order_number=order_number,
            measurement_date=measurement_date,
            cert_status=cert_status,
            sale_owner=sale_owner,
            created_by=created_by,
            disable_calibration_notification=disable_calibration_notification,
            disable_document_notification=disable_document_notification,
            disable_payment_notification=disable_payment_notification,
            cert_warning_days=cert_warning_days,  # Truyền giá trị động xuống DB
            doc_warning_days=doc_warning_days     # Truyền giá trị động xuống DB
        )
        st.cache_data.clear()

        # Ghi log giữ nguyên cấu trúc cũ của bạn
        LogRepository.add_log(
            "SYNC_ORDER",
            customer_name,
            order_number,
            f"{customer_name} | {order_number} | PaidNoti:{disable_payment_notification}"
        )

    @staticmethod
    def move_to_trash(order_number, deleted_by):
        OrderRepository.soft_delete_order(order_number, deleted_by)
        LogRepository.add_log("MOVE_TO_TRASH", "", order_number, f"Move order {order_number} to trash")

    @staticmethod
    def restore_order(order_number):
        OrderRepository.restore_order(order_number)
        LogRepository.add_log("RESTORE_ORDER", "", order_number, f"Restore order {order_number}") 

    @staticmethod
    def bulk_restore_orders(order_numbers):
        for order_number in order_numbers:
            OrderRepository.restore_order(order_number)
            LogRepository.add_log("RESTORE_ORDER", "", order_number, f"Restore order {order_number}")    

    @staticmethod
    def permanent_delete_order(order_number):
        OrderRepository.delete_order_cascade(order_number)
        LogRepository.add_log("PERMANENT_DELETE", "", order_number, f"Permanent delete order {order_number}")  

    @staticmethod
    def bulk_permanent_delete_orders(order_numbers):
        for order_number in order_numbers:
            OrderRepository.delete_order_cascade(order_number)
            LogRepository.add_log("PERMANENT_DELETE", "", order_number, f"Permanent delete order {order_number}")

    @staticmethod
    def bulk_move_to_trash(order_numbers, deleted_by):
        for order_number in order_numbers:
            OrderRepository.soft_delete_order(order_number, deleted_by)
            LogRepository.add_log("MOVE_TO_TRASH", "", order_number, f"Move order {order_number} to trash")