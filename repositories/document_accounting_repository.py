import pandas as pd
import streamlit as st
from database.pg_database import query_pg_to_dataframe, execute_pg_query
from utils.datetime_utils import convert_utc_columns

class DocumentAccountingRepository:

    @staticmethod
    @st.cache_data(ttl=15)
    def get_pending_send_to_accounting():
        """
        [GIỮ NGUYÊN GỐC 100%]
        Lấy các đơn đã nhận từ khách hàng (received_date IS NOT NULL ở bảng cũ)
        nhưng CHƯA từng được tạo luồng gửi sang kế toán ở bảng mới.
        """
        query = """
        SELECT 
            dt.id AS document_tracking_id,
            dt.order_number,
            dt.received_date AS client_received_date,
            dt.note AS tracking_note,
            o.customer_name,
            o.sale_owner,
            o.created_by
        FROM document_tracking dt
        LEFT JOIN orders o ON dt.order_number = o.order_number
        LEFT JOIN document_accounting_flows daf ON dt.id = daf.document_tracking_id
        WHERE dt.received_date IS NOT NULL 
          AND daf.document_tracking_id IS NULL
        ORDER BY dt.id DESC
        """
        df = query_pg_to_dataframe(query)
        return convert_utc_columns(df)

    @staticmethod
    def add_direct_accounting_flow(order_number, sent_date, note, username):
        """[THÊM MỚI] Gửi hồ sơ ngoài luồng - không liên quan đến document_tracking"""
        # Đi tìm thông tin phân quyền sale_owner từ bảng orders để đảm bảo không mất dữ liệu phân quyền
        query_order = "SELECT sale_owner, created_by FROM orders WHERE order_number = %s"
        df_order = query_pg_to_dataframe(query_order, (order_number,))
        
        sale_owner = df_order.iloc[0]["sale_owner"] if not df_order.empty else username
        created_by = df_order.iloc[0]["created_by"] if not df_order.empty else username

        query_insert = """
        INSERT INTO document_accounting_flows (
            document_tracking_id, order_number, sent_to_accounting_date, note, sale_owner, created_by
        ) VALUES (NULL, %s, %s, %s, %s, %s)
        """
        execute_pg_query(query_insert, (order_number, sent_date, note, sale_owner, created_by))
        
        # [YÊU CẦU 2] Ghi log hành động gửi ngoài luồng
        DocumentAccountingRepository.write_action_log(
            order_number, "SEND_DIRECT", username, f"Gửi hồ sơ NGOÀI LUỒNG. Ghi chú: {note}"
        )
        st.cache_data.clear()

    @staticmethod
    def batch_add_accounting_flow(records):
        """[GIỮ NGUYÊN GỐC] Thêm hàng loạt đơn từ luồng tự động"""
        query = """
        INSERT INTO document_accounting_flows (
            document_tracking_id, order_number, sent_to_accounting_date, note, sale_owner, created_by
        ) VALUES (%s, %s, %s, %s, %s, %s)
        """
        for r in records:
            params = (
                r["document_tracking_id"], r["order_number"], 
                r["sent_to_accounting_date"], r["note"], 
                r["sale_owner"], r["created_by"]
            )
            execute_pg_query(query, params)
        st.cache_data.clear()

    @staticmethod
    def batch_add_accounting_flow_with_log(records, username):
        """[THÊM BỔ TRỢ] Hàm bọc bên ngoài hàm batch cũ để vừa chạy logic cũ vừa ghi log audit trail"""
        # Chạy logic nạp DB cũ của bạn
        DocumentAccountingRepository.batch_add_accounting_flow(records)
        # Ghi log cho từng đơn được chọn gửi hàng loạt
        for r in records:
            DocumentAccountingRepository.write_action_log(
                r["order_number"], "SEND", username, f"Gửi hồ sơ từ hàng đợi tự động. Ghi chú: {r['note']}"
            )

    @staticmethod
    @st.cache_data(ttl=15)
    def get_all_accounting_history():
        """[GIỮ NGUYÊN GỐC] Lấy lịch sử tổng hợp"""
        query = """
        SELECT 
            daf.*,
            o.customer_name,
            dt.received_date AS client_received_date
        FROM document_accounting_flows daf
        LEFT JOIN orders o ON daf.order_number = o.order_number
        LEFT JOIN document_tracking dt ON daf.document_tracking_id = dt.id
        ORDER BY daf.id DESC
        """
        df = query_pg_to_dataframe(query)
        return convert_utc_columns(df)

    @staticmethod
    def accountant_confirm_receive(flow_id, order_number, receive_date, username):
        """[CẬP NHẬT YÊU CẦU 2] Thêm ghi log vào hàm xác nhận cũ"""
        query = """
        UPDATE document_accounting_flows
        SET accounting_received_date = %s,
            is_received_by_accounting = TRUE,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """
        execute_pg_query(query, (receive_date, flow_id))
        DocumentAccountingRepository.write_action_log(order_number, "APPROVE", username, f"Kế toán ký nhận hồ sơ. Ngày thực tế: {receive_date}")
        st.cache_data.clear()
        
    @staticmethod
    def rollback_accounting_flow(flow_id, order_number, username):
        """[SỬA LẠI] Điều phối hủy gửi hồ sơ (Xóa hẳn luồng để trả về hàng đợi chờ gửi)"""
        query = "DELETE FROM document_accounting_flows WHERE id = %s"
        execute_pg_query(query, (flow_id,))
        # Ghi log audit
        DocumentAccountingRepository.write_action_log(order_number, "UNDO", username, "Điều phối hủy/rút lại đơn đã gửi sang Kế toán")
        st.cache_data.clear()

    @staticmethod
    def reject_accounting_flow(flow_id, reject_reason, order_number, username):
        """[CẬP NHẬT YÊU CẦU 2] Thêm ghi log vào hàm từ chối cũ"""
        query = """
        UPDATE document_accounting_flows
        SET note = CONCAT('❌ Kế toán từ chối: ', %s),
            sent_to_accounting_date = NULL,
            is_received_by_accounting = FALSE,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """
        execute_pg_query(query, (reject_reason, flow_id))
        DocumentAccountingRepository.write_action_log(order_number, "REJECT", username, f"Lý do từ chối: {reject_reason}")
        st.cache_data.clear()

    @staticmethod
    def write_action_log(order_number, action_type, actor, action_details):
        """[HÀM LOG MỚI] Ghi nhật ký hệ thống"""
        query = """
        INSERT INTO document_accounting_logs (order_number, action_type, actor, action_details)
        VALUES (%s, %s, %s, %s)
        """
        try:
            execute_pg_query(query, (order_number, action_type, actor, action_details))
        except Exception:
            pass

    @staticmethod
    @st.cache_data(ttl=10)
    def get_action_logs():
        """[HÀM LOG MỚI] Đọc danh sách log hiển thị lên UI"""
        query = "SELECT order_number, action_type, actor, action_details, created_at FROM document_accounting_logs ORDER BY id DESC LIMIT 500"
        return query_pg_to_dataframe(query)
    
    @staticmethod
    def accountant_undo_receive(flow_id, order_number, username):
        """[TỐI ƯU LOGIC CẬP NHẬT GỬI LẠI] Kế toán hoàn tác hành động Duyệt/Từ chối"""
        # 1. Kiểm tra xem đơn này là đơn ngoài luồng (document_tracking_id IS NULL) 
        # hay đơn từ luồng nhận hồ sơ (HAS document_tracking_id)
        from database.pg_database import query_pg_to_dataframe, execute_pg_query
        
        check_query = "SELECT document_tracking_id FROM document_accounting_flows WHERE id = %s"
        df_check = query_pg_to_dataframe(check_query, (flow_id,))
        
        if not df_check.empty and df_check.iloc[0]["document_tracking_id"] is not None:
            # TÌNH HUỐNG A: Đơn từ luồng nhận hồ sơ (Chỗ 2)
            # Xóa hẳn khỏi luồng kế toán để giải phóng đơn quay trở lại bảng Chờ Gửi ở Chỗ 2
            delete_query = "DELETE FROM document_accounting_flows WHERE id = %s"
            execute_pg_query(delete_query, (flow_id,))
            
            DocumentAccountingRepository.write_action_log(
                order_number, "ACCOUNTANT_UNDO", username, 
                "Kế toán hoàn tác đơn từ luồng nhận hồ sơ. Đơn đã được trả về danh sách Chờ Gửi (Chỗ 2)."
            )
        else:
            # TÌNH HUỐNG B: Đơn gửi ngoài luồng (Chỗ 1)
            # Giữ nguyên dòng nhưng đưa về trạng thái chờ xác nhận để người dùng sửa đổi ở Chỗ 1
            update_query = """
            UPDATE document_accounting_flows
            SET accounting_received_date = NULL,
                is_received_by_accounting = FALSE,
                note = f'[Kế toán hoàn tác] Đang chờ cập nhật lại...',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """
            execute_pg_query(update_query, (flow_id,))
            
            DocumentAccountingRepository.write_action_log(
                order_number, "ACCOUNTANT_UNDO", username, 
                "Kế toán hoàn tác đơn ngoài luồng. Đơn đang chờ được sửa đổi/gửi lại tại Chỗ 1."
            )
            
        st.cache_data.clear()