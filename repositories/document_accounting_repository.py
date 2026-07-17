import pandas as pd
import streamlit as st
from database.pg_database import query_pg_to_dataframe, execute_pg_query
from utils.datetime_utils import convert_utc_columns
from datetime import datetime
class DocumentAccountingRepository:

    @staticmethod
    @st.cache_data(ttl=15)
    def get_pending_send_to_accounting():
        """
        [ĐÃ FIX LỖI LỌT LƯỚI]
        Lấy các đơn đã nhận từ khách hàng (received_date IS NOT NULL ở bảng cũ)
        nhưng CHƯA từng được tạo luồng gửi sang kế toán, HOẶC đã từng bị Kế toán từ chối/hoàn tác.
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
          AND (
              -- Trường hợp 1: Chưa từng gửi sang kế toán
              daf.document_tracking_id IS NULL
              OR
              -- Trường hợp 2: Đã gửi nhưng bị kế toán từ chối hoặc hoàn tác
              daf.note LIKE '❌ Kế toán từ chối:%'
              OR
              daf.note LIKE '[TỪ CHỐI_CẦN_GỬI_LẠI]%'
          )
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

        # Kiểm tra xem đơn đã tồn tại trong luồng kế toán chưa (để tránh chèn trùng dòng nếu gửi lại)
        check_query = "SELECT id FROM document_accounting_flows WHERE order_number = %s"
        df_check = query_pg_to_dataframe(check_query, (order_number,))

        if not df_check.empty:
            # Ghi đè lên dòng cũ nếu là gửi lại đơn ngoài luồng bị từ chối
            query_update = """
            UPDATE document_accounting_flows
            SET sent_to_accounting_date = %s,
                note = %s,
                is_received_by_accounting = FALSE,
                accounting_received_date = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE order_number = %s
            """
            execute_pg_query(query_update, (sent_date, note, order_number))
        else:
            # Chèn mới nếu đơn chưa từng gửi
            query_insert = """
            INSERT INTO document_accounting_flows (
                document_tracking_id, order_number, sent_to_accounting_date, note, sale_owner, created_by
            ) VALUES (NULL, %s, %s, %s, %s, %s)
            """
            execute_pg_query(query_insert, (order_number, sent_date, note, sale_owner, created_by))
        
        # Ghi log hành động gửi ngoài luồng
        DocumentAccountingRepository.write_action_log(
            order_number, "SEND_DIRECT", username, f"Gửi hồ sơ NGOÀI LUỒNG. Ghi chú: {note}"
        )
        st.cache_data.clear()

    @staticmethod
    def batch_add_accounting_flow(records):
        """[TỐI ƯU HOÁ AN TOÀN] Thêm hàng loạt đơn từ luồng tự động (Tự động cập nhật nếu gửi lại đơn bị từ chối)"""
        # Sử dụng cơ chế UPSERT (ON CONFLICT) nếu có cấu hình constraint, 
        # Hoặc cập nhật tuần tự một cách tường minh để đảm bảo an toàn tuyệt đối với mọi cấu trúc DB:
        for r in records:
            check_query = "SELECT id FROM document_accounting_flows WHERE document_tracking_id = %s"
            df_check = query_pg_to_dataframe(check_query, (r["document_tracking_id"],))
            
            if not df_check.empty:
                # Ghi đè, reset trạng thái chờ duyệt nếu là gửi lại đơn bị từ chối trước đó
                query_update = """
                UPDATE document_accounting_flows
                SET sent_to_accounting_date = %s,
                    note = %s,
                    is_received_by_accounting = FALSE,
                    accounting_received_date = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE document_tracking_id = %s
                """
                execute_pg_query(query_update, (r["sent_to_accounting_date"], r["note"], r["document_tracking_id"]))
            else:
                # Chèn mới hoàn toàn
                query_insert = """
                INSERT INTO document_accounting_flows (
                    document_tracking_id, order_number, sent_to_accounting_date, note, sale_owner, created_by
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """
                execute_pg_query(query_insert, (
                    r["document_tracking_id"], r["order_number"], 
                    r["sent_to_accounting_date"], r["note"], 
                    r["sale_owner"], r["created_by"]
                ))
        st.cache_data.clear()

    @staticmethod
    def batch_add_accounting_flow_with_log(records, username):
        """[GIỮ NGUYÊN GỐC] Hàm bọc bên ngoài hàm batch cũ để vừa chạy logic cũ vừa ghi log audit trail"""
        DocumentAccountingRepository.batch_add_accounting_flow(records)
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
        """[ĐÃ FIX AN TOÀN TRUY VẤN] Xác nhận ký nhận hồ sơ và đồng bộ sang kho lưu trữ"""
        # 1. Cập nhật luồng kế toán
        query = """
        UPDATE document_accounting_flows
        SET accounting_received_date = %s,
            is_received_by_accounting = TRUE,
            updated_at = %s
        WHERE id = %s
        """
        now = datetime.now() # Lấy chính xác ngày giờ hiện tại của máy chủ
        
        # FIX TẠI ĐÂY: Truyền đủ 3 tham số (receive_date ứng với %s số 1, now ứng với %s số 2, flow_id ứng với %s số 3)
        execute_pg_query(query, (receive_date, now, flow_id))
        
        DocumentAccountingRepository.write_action_log(
            order_number, "APPROVE", username, f"Kế toán ký nhận hồ sơ. Ngày thực tế: {receive_date}"
        )
        
        # 2. Truy vấn thông tin an toàn (Tránh lỗi UndefinedColumn nếu orders không có customer_code)
        # Đầu tiên lấy thông tin cơ bản trước
        info_query = """
            SELECT o.customer_name, daf.note 
            FROM document_accounting_flows daf
            LEFT JOIN orders o ON daf.order_number = o.order_number
            WHERE daf.id = %s
        """
        df_info = query_pg_to_dataframe(info_query, (flow_id,))
        
        if not df_info.empty:
            cust_name = df_info.iloc[0]["customer_name"] if pd.notna(df_info.iloc[0]["customer_name"]) else "Khách hàng vãng lai"
            note = df_info.iloc[0]["note"] or ""
            
            # Kiểm tra mã khách hàng (Thử lấy customer_code, nếu lỗi thì dùng mã mặc định 'KH_AUTO')
            cust_code = "KH_AUTO"
            try:
                code_query = "SELECT customer_code FROM orders WHERE order_number = %s LIMIT 1"
                df_code = query_pg_to_dataframe(code_query, (order_number,))
                if not df_code.empty and pd.notna(df_code.iloc[0]["customer_code"]):
                    cust_code = df_code.iloc[0]["customer_code"]
            except Exception:
                # Nếu bảng orders không có cột customer_code, giữ nguyên 'KH_AUTO' mà không làm sập luồng code
                pass
            
            # 3. Đồng bộ tự động sang bảng lưu trữ mới (Ghi đè luôn ngày archive_date để tránh bị NULL)
            from repositories.document_archive_repository import DocumentArchiveRepository
            DocumentArchiveRepository.add_archive_entry(
                order_number=order_number,
                customer_name=cust_name,
                customer_code=cust_code,
                document_type="Hồ sơ bàn giao kế toán",
                file_type="CHỜ FILE",
                file_path="Chưa tải lên",  
                note=f"[Đồng bộ tự động từ xác nhận kế toán] {note}",
                username=username
            )
            
        st.cache_data.clear()
        
    @staticmethod
    def rollback_accounting_flow(flow_id, order_number, username):
        """[GIỮ NGUYÊN GỐC] Điều phối hủy gửi hồ sơ"""
        query = "DELETE FROM document_accounting_flows WHERE id = %s"
        execute_pg_query(query, (flow_id,))
        DocumentAccountingRepository.write_action_log(order_number, "UNDO", username, "Điều phối hủy/rút lại đơn đã gửi sang Kế toán")
        st.cache_data.clear()

    @staticmethod
    def reject_accounting_flow(flow_id, reject_reason, order_number, username):
        """[CẬP NHẬT] Kế toán từ chối: Ẩn khỏi bảng chờ duyệt bằng cách đặt ngày gửi về NULL"""
        query = """
        UPDATE document_accounting_flows
        SET note = CONCAT('❌ Kế toán từ chối: ', %s::text),
            sent_to_accounting_date = NULL,          -- Đưa về NULL để ẩn khỏi bảng Chờ Duyệt
            is_received_by_accounting = FALSE,       -- Đánh dấu chưa nhận để Chỗ 2 có thể quét lại
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """
        execute_pg_query(query, (reject_reason, flow_id))
        DocumentAccountingRepository.write_action_log(order_number, "REJECT", username, f"Lý do từ chối: {reject_reason}")
        st.cache_data.clear()

    @staticmethod
    def write_action_log(order_number, action_type, actor, action_details):
        """[GIỮ NGUYÊN GỐC] Ghi nhật ký hệ thống"""
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
        """[GIỮ NGUYÊN GỐC] Đọc danh sách log hiển thị lên UI"""
        query = "SELECT order_number, action_type, actor, action_details, created_at FROM document_accounting_logs ORDER BY id DESC LIMIT 500"
        return query_pg_to_dataframe(query)
    
    @staticmethod
    def accountant_undo_receive(flow_id, order_number, username):
        """[GIỮ NGUYÊN GỐC] Kế toán hoàn tác nhận đơn"""
        from database.pg_database import execute_pg_query
        
        # SỬA: Thêm chữ 'f' trước dấu ba nháy và bọc chuỗi text của note bằng dấu nháy đơn '' trong SQL
        update_query = f"""
            UPDATE document_accounting_flows
            SET accounting_received_date = NULL,
                is_received_by_accounting = FALSE,
                note = 'Kế toán hoàn tác do nhấn nhầm (Thực hiện bởi: {username})',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        execute_pg_query(update_query, (flow_id,))
        
        DocumentAccountingRepository.write_action_log(
            order_number, "ACCOUNTANT_REJECT", username, 
            "Kế toán từ chối/hoàn tác đơn hàng. Yêu cầu sửa đổi và gửi lại từ luồng hồ sơ."
        )
        st.cache_data.clear()
        
    @staticmethod
    def mark_historical_done(records, username):
        """
        [THÊM MỚI BỔ TRỢ] Đánh dấu các đơn cũ trong quá khứ đã xử lý xong 
        để đóng luồng và ẩn khỏi Chỗ 2 mà không ảnh hưởng đơn mới.
        """
        import datetime
        query_insert = """
        INSERT INTO document_accounting_flows (
            document_tracking_id, order_number, sent_to_accounting_date, 
            accounting_received_date, is_received_by_accounting, note, sale_owner, created_by
        ) VALUES (%s, %s, %s, %s, TRUE, %s, %s, %s)
        """
        current_date = datetime.date.today().strftime("%Y-%m-%d")
        
        for r in records:
            # Chèn thẳng trạng thái hoàn thành (is_received_by_accounting = TRUE)
            params = (
                r["document_tracking_id"], r["order_number"], 
                current_date, current_date, 
                "[LỊCH SỬ] Đơn cũ đã xử lý xong trước khi cập nhật hệ thống.",
                r["sale_owner"], r["created_by"]
            )
            execute_pg_query(query_insert, params)
            
            # Ghi log lịch sử hệ thống để lưu vết rõ ràng
            DocumentAccountingRepository.write_action_log(
                r["order_number"], "HISTORICAL_DONE", username, 
                "Đánh dấu hoàn thành đơn cũ từ quá khứ để đóng luồng tracking."
            )
            
        st.cache_data.clear()  
        
    @staticmethod
    def get_recently_received_flows(limit=5):
        """
        [THÊM MỚI] Lấy danh sách N đơn hàng vừa được kế toán bấm Xác nhận nhận gần đây nhất
        để phục vụ tính năng Hoàn tác khẩn cấp khi bảng chờ duyệt trống.
        """
        from database.pg_database import execute_pg_query
        import pandas as pd
        
        query = """
            SELECT id, order_number, document_tracking_id, accounting_received_date, note, sale_owner
            FROM document_accounting_flows
            WHERE is_received_by_accounting = TRUE
            ORDER BY updated_at DESC
            LIMIT %s
        """
        rows = execute_pg_query(query, (limit,))
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame(rows)
    
        
    @staticmethod
    def clear_all_action_logs(username):
        """
        [THÊM MỚI] Xóa toàn bộ log lịch sử thao tác sau khi đã backup.
        Vẫn lưu lại 1 dòng log đánh dấu hành động xóa này để làm bằng chứng (audit trail).
        """
        from database.pg_database import execute_pg_query
        # 1. Xóa sạch bảng log cũ
        delete_query = "DELETE FROM document_accounting_logs"
        execute_pg_query(delete_query)
        
        # 2. Ghi nhận vết của người đã xóa hệ thống log
        DocumentAccountingRepository.write_action_log(
            "SYSTEM_CLEANUP", "CLEAR_LOGS", username, 
            "Người dùng đã thực hiện dọn dẹp sạch toàn bộ lịch sử log kế toán."
        )
        st.cache_data.clear()      