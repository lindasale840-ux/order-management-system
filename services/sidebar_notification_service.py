from services.finance_service import FinanceService
from repositories.document_tracking_repository import DocumentTrackingRepository
from repositories.order_repository import OrderRepository # <-- Import thêm Repository này để lấy ngày cấu hình động
import pandas as pd
from config.app_config import DOCUMENT_WARNING_DAYS
import streamlit as st

class SidebarNotificationService:

    @staticmethod
    def get_alert_summary(username: str):
        # Lấy thông tin định danh phân quyền hiện tại từ session_state
        current_role = st.session_state.get("role")
        current_owner = st.session_state.get("sale_owner")
        
        # 1. Gọi hàm lấy dữ liệu tài chính chính xác
        df = FinanceService.build_finance_dataframe(role=current_role, username=username, sale_owner=current_owner)

        # 2. ĐỒNG BỘ CỘT CẤU HÌNH CẢNH BÁO TỪ DATABASE (Đồng nhất với trang thông báo)
        try:
            all_orders_db = OrderRepository.get_all_orders()
            if not all_orders_db.empty and "order_number" in df.columns:
                cert_map = all_orders_db.set_index("order_number")["cert_warning_days"].to_dict()
                doc_map = all_orders_db.set_index("order_number")["doc_warning_days"].to_dict()
                
                df["cert_warning_days"] = df["order_number"].map(cert_map)
                df["doc_warning_days"] = df["order_number"].map(doc_map)
        except Exception:
            if "cert_warning_days" not in df.columns:
                df["cert_warning_days"] = None
            if "doc_warning_days" not in df.columns:
                df["doc_warning_days"] = None

        # Tính toán các chỉ số cơ bản của các tab khác (Giữ nguyên gốc logic cũ)
        missing_cert = len(
            df[df["cert_workflow_status"] == "Missing Cert"]
        )

        payment_overdue = len(
            df[
                (df["payment_overdue"] == "Overdue")
                & (df["disable_payment_notification"] != 1)
            ]
        )

        due_soon = len(
            df[df["cert_due_soon"] == "Due Soon"]
        )

        missing_invoice = len(
            df[df["order_status"] == "Missing Invoice"]
        )

        missing_send = 0
        pending_return = 0

        # Lấy dữ liệu theo dõi gửi nhận hồ sơ
        tracking_df = DocumentTrackingRepository.get_latest_tracking()
        
        allowed_orders = set(
            df["order_number"].astype(str)
        )

        tracking_df = tracking_df[
            tracking_df["order_number"].astype(str)
            .isin(allowed_orders)
        ]
        
        # Khử múi giờ ngày hôm nay để so sánh chuẩn xác
        today = pd.Timestamp.today().normalize()

        # ========================================================
        # Missing Send (Tab 5) - ĐỒNG BỘ LOGIC TÍNH ĐỘNG
        # ========================================================
        sent_orders = set()
        if not tracking_df.empty:
            sent_orders = set(tracking_df["order_number"].astype(str))

        cert_orders_df = df[df["cert_status"].notna()].copy()
        
        # Khử múi giờ cert_status
        cert_orders_df["cert_status"] = pd.to_datetime(
            cert_orders_df["cert_status"],
            errors="coerce"
        ).dt.tz_localize(None)

        ignore_orders = set(
            df[df["disable_document_notification"] == 1]["order_number"]
        )

        # Sử dụng hàm kiểm tra động giống hệt trang thông báo
        def is_document_overdue(row):
            if pd.isna(row["cert_status"]):
                return False
            row_doc_days = row.get("doc_warning_days")
            try:
                limit_days = int(row_doc_days) if pd.notna(row_doc_days) and int(row_doc_days) > 0 else DOCUMENT_WARNING_DAYS
            except:
                limit_days = DOCUMENT_WARNING_DAYS
            
            days_diff = (today - row["cert_status"]).days
            return days_diff > limit_days

        if not cert_orders_df.empty:
            overdue_mask = cert_orders_df.apply(is_document_overdue, axis=1)
            missing_send_df = cert_orders_df[
                overdue_mask
                & ~cert_orders_df["order_number"].astype(str).isin(sent_orders)
                & ~cert_orders_df["order_number"].astype(str).isin(ignore_orders)
            ]
            missing_send = len(missing_send_df)
        else:
            missing_send = 0

        # ========================================================
        # Pending Return (Tab 6) - ĐỒNG BỘ LOGIC TÍNH ĐỘNG
        # ========================================================
        if not tracking_df.empty:
            # Khử múi giờ ngày gửi/ngày nhận
            tracking_df["sent_date"] = pd.to_datetime(
                tracking_df["sent_date"],
                errors="coerce"
            ).dt.tz_localize(None)
            
            tracking_df["received_date"] = pd.to_datetime(
                tracking_df["received_date"],
                errors="coerce"
            ).dt.tz_localize(None)

            doc_days_mapping = df.set_index("order_number")["doc_warning_days"].to_dict()

            def is_pending_return_overdue(row):
                if pd.isna(row["sent_date"]) or pd.notna(row["received_date"]):
                    return False
                
                order_num = row["order_number"]
                row_doc_days = doc_days_mapping.get(order_num)
                
                try:
                    limit_days = int(row_doc_days) if pd.notna(row_doc_days) and int(row_doc_days) > 0 else DOCUMENT_WARNING_DAYS
                except:
                    limit_days = DOCUMENT_WARNING_DAYS
                
                days_diff = (today - row["sent_date"]).days
                return days_diff > limit_days

            overdue_pending_mask = tracking_df.apply(is_pending_return_overdue, axis=1)
            pending_return_df = tracking_df[overdue_pending_mask]
            
            pending_return_df = pending_return_df[
                ~pending_return_df["order_number"].astype(str).isin(ignore_orders)
            ]

            pending_return = len(pending_return_df)

        # Tính tổng số thông báo chính xác
        total_alert = (
            missing_cert
            + payment_overdue
            + due_soon
            + missing_invoice
            + missing_send
            + pending_return
        )

        return {
            "total": total_alert,
            "missing_cert": missing_cert,
            "payment_overdue": payment_overdue,
            "due_soon": due_soon,
            "missing_invoice": missing_invoice,
            "missing_send": missing_send,
            "pending_return": pending_return
        }