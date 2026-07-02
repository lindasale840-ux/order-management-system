from typing import List, Dict, Optional
from database.connection import SessionLocal
from sqlalchemy import text

class NoteRepository:
    """Repository xử lý các thao tác với bảng notes"""
    
    @staticmethod
    def get_notes(user_id: int, is_admin: bool = False) -> List[Dict]:
        """Lấy danh sách ghi chú"""
        with SessionLocal() as session:
            if is_admin:
                query = text("""
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
                """)
                result = session.execute(query)
            else:
                query = text("""
                    SELECT 
                        n.*,
                        u.username as created_by_username,
                        u.role as created_by_role
                    FROM notes n
                    LEFT JOIN users u ON n.user_id = u.id
                    WHERE n.user_id = :user_id
                    ORDER BY 
                        CASE n.priority
                            WHEN 'critical' THEN 1
                            WHEN 'high' THEN 2
                            WHEN 'medium' THEN 3
                            WHEN 'low' THEN 4
                        END,
                        n.created_at DESC
                """)
                result = session.execute(query, {"user_id": user_id})
            
            return [dict(row._mapping) for row in result]
    
    @staticmethod
    def get_note_by_id(note_id: int) -> Optional[Dict]:
        """Lấy thông tin một ghi chú theo ID"""
        with SessionLocal() as session:
            query = text("SELECT * FROM notes WHERE id = :note_id")
            result = session.execute(query, {"note_id": note_id}).first()
            return dict(result._mapping) if result else None
    
    @staticmethod
    def create_note(data: Dict) -> int:
        """Tạo ghi chú mới"""
        with SessionLocal() as session:
            query = text("""
                INSERT INTO notes (
                    user_id, title, content, category, 
                    priority, layer, status, due_date
                ) VALUES (
                    :user_id, :title, :content, :category,
                    :priority, :layer, :status, :due_date
                )
            """)
            result = session.execute(query, data)
            session.commit()
            return result.lastrowid
    
    @staticmethod
    def update_note(note_id: int, data: Dict) -> bool:
        """Cập nhật ghi chú"""
        with SessionLocal() as session:
            query = text("""
                UPDATE notes 
                SET 
                    title = :title,
                    content = :content,
                    category = :category,
                    priority = :priority,
                    layer = :layer,
                    status = :status,
                    due_date = :due_date,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :note_id
            """)
            data['note_id'] = note_id
            result = session.execute(query, data)
            session.commit()
            return result.rowcount > 0
    
    @staticmethod
    def delete_note(note_id: int, user_id: int = None, is_admin: bool = False) -> bool:
        """Xóa ghi chú"""
        with SessionLocal() as session:
            if is_admin:
                query = text("DELETE FROM notes WHERE id = :note_id")
                result = session.execute(query, {"note_id": note_id})
            else:
                query = text("DELETE FROM notes WHERE id = :note_id AND user_id = :user_id")
                result = session.execute(query, {
                    "note_id": note_id,
                    "user_id": user_id
                })
            session.commit()
            return result.rowcount > 0
    
    @staticmethod
    def mark_as_read(note_id: int, user_id: int) -> bool:
        """Đánh dấu ghi chú đã đọc"""
        with SessionLocal() as session:
            query = text("""
                UPDATE notes 
                SET is_read = 1 
                WHERE id = :note_id AND user_id = :user_id
            """)
            result = session.execute(query, {
                "note_id": note_id,
                "user_id": user_id
            })
            session.commit()
            return result.rowcount > 0
    
    @staticmethod
    def mark_as_unread(note_id: int, user_id: int) -> bool:
        """Đánh dấu ghi chú chưa đọc"""
        with SessionLocal() as session:
            query = text("""
                UPDATE notes 
                SET is_read = 0 
                WHERE id = :note_id AND user_id = :user_id
            """)
            result = session.execute(query, {
                "note_id": note_id,
                "user_id": user_id
            })
            session.commit()
            return result.rowcount > 0
    
    @staticmethod
    def count_unread(user_id: int) -> int:
        """Đếm số ghi chú chưa đọc của user"""
        with SessionLocal() as session:
            query = text("""
                SELECT COUNT(*) FROM notes 
                WHERE user_id = :user_id AND is_read = 0
            """)
            result = session.execute(query, {"user_id": user_id}).scalar()
            return result or 0
    
    @staticmethod
    def get_statistics(user_id: int, is_admin: bool = False) -> Dict:
        """Lấy thống kê về ghi chú"""
        with SessionLocal() as session:
            if is_admin:
                query = text("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                        SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
                        SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) as done,
                        SUM(CASE WHEN is_read = 0 THEN 1 ELSE 0 END) as unread
                    FROM notes
                """)
                result = session.execute(query).first()
            else:
                query = text("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                        SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
                        SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) as done,
                        SUM(CASE WHEN is_read = 0 THEN 1 ELSE 0 END) as unread
                    FROM notes
                    WHERE user_id = :user_id
                """)
                result = session.execute(query, {"user_id": user_id}).first()
            
            return {
                'total': result[0] or 0,
                'pending': result[1] or 0,
                'in_progress': result[2] or 0,
                'done': result[3] or 0,
                'unread': result[4] or 0
            }