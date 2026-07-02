import streamlit as st
from typing import List, Dict

def render_notification_badge():
    """Hiển thị biểu tượng chuông với số lượng ghi chú chưa đọc"""
    from services.note_service import NoteService
    
    if 'username' not in st.session_state:
        return
    
    user_id = st.session_state.get('user_id')
    if not user_id:
        return
    
    unread_count = NoteService.count_unread(user_id)
    
    st.markdown("""
        <style>
        .notification-bell-container {
            position: fixed;
            top: 20px;
            right: 30px;
            z-index: 999;
            cursor: pointer;
        }
        .notification-bell {
            font-size: 28px;
            color: #f1f5f9;
            background: #1e293b;
            padding: 10px 14px;
            border-radius: 50%;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 2px solid #334155;
            position: relative;
            text-decoration: none;
        }
        .notification-bell:hover {
            transform: scale(1.05);
            border-color: #38bdf8;
            box-shadow: 0 4px 20px rgba(56, 189, 248, 0.2);
        }
        .notification-badge {
            position: absolute;
            top: -5px;
            right: -5px;
            background: #ef4444;
            color: white;
            border-radius: 50%;
            padding: 2px 8px;
            font-size: 12px;
            font-weight: bold;
            min-width: 20px;
            text-align: center;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
        }
        .notification-badge.zero {
            background: #22c55e;
        }
        </style>
    """, unsafe_allow_html=True)
    
    badge_class = "notification-badge zero" if unread_count == 0 else "notification-badge"
    badge_text = "" if unread_count == 0 else str(unread_count)
    
    st.markdown(f"""
        <div class="notification-bell-container">
            <a href="?page=notes" class="notification-bell" title="Ghi chú">
                🔔
                <span class="{badge_class}">{badge_text}</span>
            </a>
        </div>
    """, unsafe_allow_html=True)

def render_notes_summary(stats: Dict):
    """Hiển thị dòng tổng hợp ở đầu page"""
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            label="📋 Tổng số",
            value=stats['total'],
            help="Tổng số ghi chú của bạn"
        )
    with col2:
        st.metric(
            label="⏳ Đang chờ",
            value=stats['pending'],
            help="Ghi chú đang chờ xử lý"
        )
    with col3:
        st.metric(
            label="🔄 Đang làm",
            value=stats['in_progress'],
            help="Ghi chú đang thực hiện"
        )
    with col4:
        st.metric(
            label="✅ Hoàn thành",
            value=stats['done'],
            help="Ghi chú đã hoàn thành"
        )
    with col5:
        unread = stats.get('unread', 0)
        st.metric(
            label="🔔 Chưa đọc",
            value=unread,
            help="Số ghi chú chưa đọc",
            delta=f"{unread} chưa xem" if unread > 0 else None
        )

def render_note_card(note: dict, is_admin: bool = False):
    """Hiển thị một ghi chú dạng card hoàn toàn an toàn với Streamlit"""
    import streamlit as st

    priority_colors = {
        'critical': ('#dc2626', '🔴'),
        'high': ('#f97316', '🟠'),
        'medium': ('#eab308', '🟡'),
        'low': ('#22c55e', '🟢')
    }
    color, icon = priority_colors.get(note.get('priority', 'general'), ('#64748b', '⚪'))
    
    status_map = {
        'pending': ('⏳', 'Đang chờ'),
        'in_progress': ('🔄', 'Đang làm'),
        'done': ('✅', 'Hoàn thành')
    }
    status_icon, status_text = status_map.get(note.get('status', 'pending'), ('❓', 'Khác'))
    
    # Định nghĩa sẵn các đoạn HTML nhỏ để không dùng ngoặc nhọn CSS bên trong f-string chính
    badge_style = f"background: {color}20; color: {color}; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: 500;"
    badge_html = f'<span style="{badge_style}">{status_icon} {status_text}</span>'
    
    if note.get('is_read'):
        read_status_html = '<span style="color: #22c55e; font-weight: 500; margin-left: 10px;">✅ Đã đọc</span>'
    else:
        read_status_html = '<span style="color: #ef4444; font-weight: 500; margin-left: 10px;">🔔 Chưa đọc</span>'

    note_title = note.get('title', 'Không tiêu đề')
    note_content = note.get('content', '<i style="color: #94a3b8;">Không có nội dung</i>')
    
    # Tạo chuỗi HTML thuần túy, sạch sẽ, không chứa thuộc tính CSS dùng ngoặc nhọn trực tiếp
    card_html = f"""
        <div style="background: white; border-radius: 12px; padding: 20px; margin: 12px 0; border-left: 5px solid {color}; box-shadow: 0 2px 8px rgba(0,0,0,0.06);">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                <span style="font-size: 18px; font-weight: 600; color: #1e293b;">{icon} {note_title}</span>
                {badge_html}
            </div>
            <div style="color: #475569; font-size: 14px; margin: 8px 0; line-height: 1.6;">
                {note_content}
            </div>
            <div style="font-size: 13px; color: #64748b; margin-top: 8px;">
                <span>🏷️ Loại: {note.get('category', 'Chung')}</span>
                {read_status_html}
            </div>
        </div>
    """
    
    # Ép Streamlit chạy chế độ HTML tuyệt đối
    st.markdown(card_html, unsafe_allow_html=True)

def render_quick_actions():
    """Hiển thị các nút hành động nhanh"""
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("📝 Tạo ghi chú mới", use_container_width=True, type="primary"):
            st.session_state['show_create_note'] = True
            st.rerun()
    with col2:
        if st.button("🔄 Làm mới", use_container_width=True):
            st.rerun()