from typing import List, Dict, Optional
import pandas as pd
from database.pg_database import query_pg_to_dataframe, execute_pg_query

class NoteRepository:
    """Repository xử lý các thao tác với bảng notes"""
    
    @staticmethod
    def get_notes(user_id: int, is_admin: bool = False) -> List[Dict]:
        """Lấy danh sách ghi chú"""
        if is_admin:
            query = """
                SELECT 
                    n.*,
                    u.username as created_by_username,
                    u.role as created_by_role
                FROM notes n
                LEFT JOIN users u ON n.user_id = u.id
                ORDER BY 
                    CASE n.priority
                        WHEN 'critical' THEN 1
                        WHEN 'high' THEN 2
                        WHEN 'medium' THEN 3
                        WHEN 'low' THEN 4
                    END,
                    n.created_at DESC
            """
            df = query_pg_to_dataframe(query)
        else:
            query = """
                SELECT 
                    n.*,
                    u.username as created_by_username,
                    u.role as created_by_role
                FROM notes n
                LEFT JOIN users u ON n.user_id = u.id
                WHERE n.user_id = %s
                ORDER BY 
                    CASE n.priority
                        WHEN 'critical' THEN 1
                        WHEN 'high' THEN 2
                        WHEN 'medium' THEN 3
                        WHEN 'low' THEN 4
                    END,
                    n.created_at DESC
            """
            df = query_pg_to_dataframe(query, (user_id,))
        
        return df.to_dict(orient='records')
    
    @staticmethod
    def get_note_by_id(note_id: int) -> Optional[Dict]:
        """Lấy thông tin một ghi chú theo ID"""
        query = "SELECT * FROM notes WHERE id = %s"
        df = query_pg_to_dataframe(query, (note_id,))
        if not df.empty:
            return df.into_dict(orient='records')[0] if hasattr(df, 'into_dict') else df.to_dict(orient='records')[0]
        return None
    
    @staticmethod
    def create_note(data: Dict) -> int:
        """Tạo ghi chú mới và trả về ID vừa tạo trên Postgres"""
        query = """
            INSERT INTO notes (
                user_id, title, content, category, 
                priority, layer, status, due_date
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s
            )
            RETURNING id;
        """
        
        # Ép kiểu layer về int (ví dụ: nếu là "Data" hoặc lỗi thì chuyển thành 1)
        try:
            layer_val = int(data.get('layer'))
        except (ValueError, TypeError):
            layer_val = 1  # Giá trị mặc định dạng số nguyên cho cột layer trong DB của bạn
            
        params = (
            data.get('user_id'), 
            data.get('title'), 
            data.get('content'), 
            data.get('category'),
            data.get('priority'), 
            layer_val,             # Truyền số nguyên vào đây để khớp kiểu INTEGER
            data.get('status'), 
            data.get('due_date')
        )
        
        df = query_pg_to_dataframe(query, params)
        if not df.empty:
            return int(df.iloc[0]['id'])
        return 0

    @staticmethod
    def update_note(note_id: int, data: Dict) -> bool:
        """Cập nhật ghi chú"""
        query = """
            UPDATE notes 
            SET 
                title = %s,
                content = %s,
                category = %s,
                priority = %s,
                layer = %s,
                status = %s,
                due_date = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        try:
            layer_val = int(data.get('layer'))
        except (ValueError, TypeError):
            layer_val = 1
            
        params = (
            data.get('title'), 
            data.get('content'), 
            data.get('category'),
            data.get('priority'), 
            layer_val, 
            data.get('status'), 
            data.get('due_date'), 
            note_id
        )
        row_count = execute_pg_query(query, params)
        return (row_count or 0) > 0 if row_count is not None else True
    
    @staticmethod
    def delete_note(note_id: int, user_id: int = None, is_admin: bool = False) -> bool:
        """Xóa ghi chú"""
        if is_admin:
            query = "DELETE FROM notes WHERE id = %s"
            row_count = execute_pg_query(query, (note_id,))
        else:
            query = "DELETE FROM notes WHERE id = %s AND user_id = %s"
            row_count = execute_pg_query(query, (note_id, user_id))
        return (row_count or 0) > 0 if row_count is not None else True
    
    @staticmethod
    def mark_as_read(note_id: int, user_id: int) -> bool:
        """Đánh dấu ghi chú đã đọc"""
        query = """
            UPDATE notes 
            SET is_read = 1 
            WHERE id = %s AND user_id = %s
        """
        row_count = execute_pg_query(query, (note_id, user_id))
        return (row_count or 0) > 0 if row_count is not None else True
    
    @staticmethod
    def mark_as_unread(note_id: int, user_id: int) -> bool:
        """Đánh dấu ghi chú chưa đọc"""
        query = """
            UPDATE notes 
            SET is_read = 0 
            WHERE id = %s AND user_id = %s
        """
        row_count = execute_pg_query(query, (note_id, user_id))
        return (row_count or 0) > 0 if row_count is not None else True
    
    @staticmethod
    def count_unread(user_id: int) -> int:
        """Đếm số ghi chú chưa đọc của user"""
        query = """
            SELECT COUNT(*) as count FROM notes 
            WHERE user_id = %s AND is_read = 0
        """
        df = query_pg_to_dataframe(query, (user_id,))
        if not df.empty:
            return int(df.iloc[0]['count'])
        return 0
    
    @staticmethod
    def get_statistics(user_id: int, is_admin: bool = False) -> Dict:
        """Lấy thống kê về ghi chú"""
        if is_admin:
            query = """
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
                    SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) as done,
                    SUM(CASE WHEN is_read = 0 THEN 1 ELSE 0 END) as unread
                FROM notes
            """
            df = query_pg_to_dataframe(query)
        else:
            query = """
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
                    SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) as done,
                    SUM(CASE WHEN is_read = 0 THEN 1 ELSE 0 END) as unread
                FROM notes
                WHERE user_id = %s
            """
            df = query_pg_to_dataframe(query, (user_id,))
        
        if not df.empty:
            row = df.iloc[0]
            return {
                'total': int(row['total']) if pd.notna(row['total']) else 0,
                'pending': int(row['pending']) if pd.notna(row['pending']) else 0,
                'in_progress': int(row['in_progress']) if pd.notna(row['in_progress']) else 0,
                'done': int(row['done']) if pd.notna(row['done']) else 0,
                'unread': int(row['unread']) if pd.notna(row['unread']) else 0
            }
        return {'total': 0, 'pending': 0, 'in_progress': 0, 'done': 0, 'unread': 0}