import streamlit as st
from repositories.document_accounting_repository import DocumentAccountingRepository
from repositories.log_repository import LogRepository

class DocumentAccountingService:

    @staticmethod
    def send_documents_to_accounting(selected_rows, sent_date, note):
        """Đóng gói dữ liệu và đẩy xuống Repo + Ghi nhận hệ thống log của bạn"""
        records_to_insert = []
        for row in selected_rows:
            records_to_insert.append({
                "document_tracking_id": int(row["document_tracking_id"]),
                "order_number": str(row["order_number"]),
                "sent_to_accounting_date": sent_date,
                "note": note,
                "sale_owner": row.get("sale_owner"),
                "created_by": row.get("created_by")
            })
            
            # Tận dụng Log System có sẵn của bạn để lưu vết lịch sử hành động
            LogRepository.add_log(
                "SEND_TO_ACCOUNTING",
                "",
                str(row["order_number"]),
                f"sent_date={sent_date} | tracking_id={row['document_tracking_id']}"
            )
            
        if records_to_insert:
            DocumentAccountingRepository.batch_add_accounting_flow(records_to_insert)

    @staticmethod
    def confirm_receipt_by_accountant(flow_id, order_number, receive_date):
        """Kế toán ký nhận bàn giao hồ sơ"""
        DocumentAccountingRepository.accountant_confirm_receive(flow_id, receive_date)
        LogRepository.add_log(
            "ACCOUNTANT_CONFIRMED",
            "",
            str(order_number),
            f"received_date={receive_date} | flow_id={flow_id}"
        )