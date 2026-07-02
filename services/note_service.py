from typing import List, Dict, Optional
from repositories.note_repository import NoteRepository

class NoteService:
    """Service xử lý logic nghiệp vụ cho ghi chú"""
    
    @staticmethod
    def get_notes(user_id: int, role: str) -> List[Dict]:
        """Lấy danh sách ghi chú với phân quyền"""
        is_admin = role == "ADMIN"
        return NoteRepository.get_notes(user_id, is_admin)
    
    @staticmethod
    def get_note_by_id(note_id: int, user_id: int, role: str) -> Optional[Dict]:
        """Lấy chi tiết một ghi chú"""
        note = NoteRepository.get_note_by_id(note_id)
        if not note:
            return None
        
        is_admin = role == "ADMIN"
        if not is_admin and note['user_id'] != user_id:
            return None
        
        return note
    
    @staticmethod
    def create_note(user_id: int, data: Dict) -> Dict:
        """Tạo ghi chú mới"""
        note_data = {
            'user_id': user_id,
            'title': data['title'].strip(),
            'content': data.get('content', '').strip(),
            'category': data.get('category', 'general'),
            'priority': data.get('priority', 'medium'),
            'layer': data.get('layer', 1),
            'status': data.get('status', 'pending'),
            'due_date': data.get('due_date')
        }
        
        note_id = NoteRepository.create_note(note_data)
        return {
            'success': True,
            'id': note_id,
            'message': 'Tạo ghi chú thành công!'
        }
    
    @staticmethod
    def update_note(note_id: int, user_id: int, role: str, data: Dict) -> Dict:
        """Cập nhật ghi chú"""
        note = NoteRepository.get_note_by_id(note_id)
        if not note:
            return {'success': False, 'message': 'Không tìm thấy ghi chú'}
        
        is_admin = role == "ADMIN"
        if not is_admin and note['user_id'] != user_id:
            return {'success': False, 'message': 'Bạn không có quyền sửa ghi chú này'}
        
        update_data = {
            'title': data['title'].strip(),
            'content': data.get('content', '').strip(),
            'category': data.get('category', 'general'),
            'priority': data.get('priority', 'medium'),
            'layer': data.get('layer', 1),
            'status': data.get('status', 'pending'),
            'due_date': data.get('due_date')
        }
        
        success = NoteRepository.update_note(note_id, update_data)
        if success:
            return {'success': True, 'message': 'Cập nhật ghi chú thành công!'}
        return {'success': False, 'message': 'Không thể cập nhật ghi chú'}
    
    @staticmethod
    def delete_note(note_id: int, user_id: int, role: str) -> Dict:
        """Xóa ghi chú"""
        is_admin = role == "ADMIN"
        success = NoteRepository.delete_note(note_id, user_id, is_admin)
        
        if success:
            return {'success': True, 'message': 'Xóa ghi chú thành công!'}
        return {'success': False, 'message': 'Không thể xóa ghi chú'}
    
    @staticmethod
    def toggle_read_status(note_id: int, user_id: int, current_status: bool) -> Dict:
        """Chuyển đổi trạng thái đã đọc/chưa đọc"""
        if current_status:
            success = NoteRepository.mark_as_unread(note_id, user_id)
            message = 'Đã đánh dấu chưa đọc'
        else:
            success = NoteRepository.mark_as_read(note_id, user_id)
            message = 'Đã đánh dấu đã đọc'
        
        if success:
            return {'success': True, 'message': message}
        return {'success': False, 'message': 'Không thể cập nhật trạng thái'}
    
    @staticmethod
    def get_statistics(user_id: int, role: str) -> Dict:
        """Lấy thống kê ghi chú"""
        is_admin = role == "ADMIN"
        return NoteRepository.get_statistics(user_id, is_admin)
    
    @staticmethod
    def count_unread(user_id: int) -> int:
        """Đếm số ghi chú chưa đọc"""
        return NoteRepository.count_unread(user_id)