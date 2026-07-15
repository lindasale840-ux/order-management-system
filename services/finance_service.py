import pandas as pd
import streamlit as st
from repositories.order_repository import OrderRepository
from repositories.payment_repository import PaymentRepository
from utils.data_permission import filter_by_sale_owner
from config.app_config import DOCUMENT_WARNING_DAYS # Đảm bảo import để làm giá trị fallback mặc định

class FinanceService:

    @staticmethod
    @st.cache_data(show_spinner="Đang xử lý dữ liệu tài chính...")
    def build_finance_dataframe(role=None, username=None, sale_owner=None):
        print(f"FinanceService.build_finance_dataframe() kích hoạt cho User: {username} | Role: {role}")

        # 1. Lấy dữ liệu từ tầng Repository
        orders_df = OrderRepository.get_all_orders()
        orders_df = filter_by_sale_owner(orders_df, role=role, username=username, sale_owner=sale_owner)
        payments_df = PaymentRepository.get_all_payments()

        # 2. Gộp dữ liệu
        df = pd.merge(
            orders_df,
            payments_df,
            on="order_number",
            how="left",
            suffixes=("_order", "_payment")
        )

        today = pd.Timestamp.today()
        
        # 3. Chuẩn hóa các cột dữ liệu sang dạng số và ngày tháng
        df["payment_terms"] = pd.to_numeric(df["payment_terms"], errors="coerce").fillna(0)
        df["measurement_date"] = pd.to_datetime(df["measurement_date"], errors="coerce")
        df["cert_status"] = pd.to_datetime(df["cert_status"], errors="coerce")
        df["invoice_date"] = pd.to_datetime(df["invoice_date"], errors="coerce")
        df["payment_status"] = pd.to_datetime(df["payment_status"], errors="coerce")

        # Ép kiểu dữ liệu cấu hình cảnh báo mới (Tránh lỗi do dữ liệu trống)
        if "cert_warning_days" in df.columns:
            df["cert_warning_days"] = pd.to_numeric(df["cert_warning_days"], errors="coerce")
        if "doc_warning_days" in df.columns:
            df["doc_warning_days"] = pd.to_numeric(df["doc_warning_days"], errors="coerce")

        order_status_list = []
        payment_overdue_list = []
        payment_status_text_list = []
        cert_overdue_list = []
        cert_due_soon_list = []
        cert_workflow_status_list = []

        # 4. Tính toán các cột trạng thái
        for _, row in df.iterrows():
            # ĐỌC ĐỘNG cảnh báo trễ hạn Cert. Nếu trống thì fallback về 5 ngày.
            row_cert_days = row.get("cert_warning_days")
            cert_days_limit = int(row_cert_days) if pd.notna(row_cert_days) and row_cert_days > 0 else 5

            if (
                pd.isna(row["invoice_date"])
                and pd.notna(row["cert_status"])
                and (today - row["cert_status"]).days > 5
            ):
                order_status = "Missing Invoice"
            else:
                order_status = "OK"
            order_status_list.append(order_status)

            if pd.notna(row["payment_status"]):
                payment_overdue = "No"
            elif pd.isna(row["invoice_date"]):
                payment_overdue = "Wait Invoice"
            else:
                payment_terms = pd.to_numeric(row["payment_terms"], errors="coerce")
                if pd.isna(payment_terms):
                    payment_terms = 0
                payment_terms = max(0, min(int(payment_terms), 365))
                due_date = row["invoice_date"] + pd.Timedelta(days=payment_terms)

                if today > due_date:
                    payment_overdue = "Overdue"
                else:
                    payment_overdue = "Pending"
            payment_overdue_list.append(payment_overdue)

            if pd.notna(row["payment_status"]):
                payment_status_text = "Paid"
            else:
                payment_status_text = "Pending"
            payment_status_text_list.append(payment_status_text)

            # SỬA: Thay thế số 5 cứng bằng biến động cert_days_limit
            if pd.isna(row["cert_status"]):
                if pd.notna(row["measurement_date"]) and (today - row["measurement_date"]).days > cert_days_limit:
                    cert_workflow_status = "Missing Cert"
                else:
                    cert_workflow_status = "Processing Cert"
            else:
                cert_workflow_status = "Cert Completed"
            cert_workflow_status_list.append(cert_workflow_status)

            if row.get("disable_calibration_notification", 0) == 1:
                cert_overdue = "Ignore"
                cert_due_soon = "Ignore"
            else:
                if pd.notna(row["measurement_date"]):
                    calibration_due = row["measurement_date"] + pd.DateOffset(months=11)
                    remaining_days = (calibration_due - today).days

                    if remaining_days < 0:
                        cert_overdue = "Overdue"
                    else:
                        cert_overdue = "OK"

                    if 0 <= remaining_days <= 30:
                        cert_due_soon = "Due Soon"
                    else:
                        cert_due_soon = "No"
                else:
                    cert_overdue = "Unknown"
                    cert_due_soon = "Unknown"

            cert_overdue_list.append(cert_overdue)
            cert_due_soon_list.append(cert_due_soon)

        # 5. Gán lại các mảng kết quả vào DataFrame
        df["order_status"] = order_status_list
        df["payment_overdue"] = payment_overdue_list
        df["payment_status_text"] = payment_status_text_list
        df["cert_overdue"] = cert_overdue_list
        df["cert_due_soon"] = cert_due_soon_list
        df["cert_workflow_status"] = cert_workflow_status_list

        return df