import streamlit as st
from services.note_service import NoteService
from components.note_components import (
    render_notes_summary,
    render_note_card,
    render_quick_actions
)

def show_notes_page():
    """Trang quản lý ghi chú"""
    
    if 'username' not in st.session_state:
        st.warning("Vui lòng đăng nhập để xem ghi chú")
        return
    
    # ✅ Lấy user_id từ session (đã có sau khi login)
    user_id = st.session_state.get('user_id')
    if not user_id:
        st.error("Không tìm thấy ID người dùng. Vui lòng đăng nhập lại.")
        return
    role = st.session_state.get('role', '')
    is_admin = role == "ADMIN"
    
    st.title("📋 Quản lý Ghi chú")
    st.caption("Quản lý và theo dõi các ghi chú công việc của bạn")
    st.divider()
    
    stats = NoteService.get_statistics(user_id, role)
    render_notes_summary(stats)
    st.divider()
    
    render_quick_actions()
    st.divider()
    
    # Tạo ghi chú mới
    if st.session_state.get('show_create_note', False):
        with st.expander("📝 Tạo ghi chú mới", expanded=True):
            with st.form("create_note_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    title = st.text_input("Tiêu đề *", placeholder="Nhập tiêu đề ghi chú")
                    category = st.selectbox(
                        "Loại ghi chú",
                        [
                            ('work', '💼 Công việc'),
                            ('personal', '👤 Cá nhân'),
                            ('project', '📊 Dự án'),
                            ('urgent', '🚨 Khẩn cấp'),
                            ('general', '📝 Chung')
                        ],
                        format_func=lambda x: x[1]
                    )[0]
                    
                with col2:
                    priority = st.selectbox(
                        "Mức độ ưu tiên",
                        [
                            ('critical', '🔴 Cực kỳ quan trọng'),
                            ('high', '🟠 Quan trọng'),
                            ('medium', '🟡 Bình thường'),
                            ('low', '🟢 Thấp')
                        ],
                        format_func=lambda x: x[1]
                    )[0]
                    layer = st.selectbox(
                        "Lớp theo dõi",
                        [1, 2, 3, 4, 5],
                        format_func=lambda x: f"🌟 Lớp {x}"
                    )
                
                content = st.text_area(
                    "Nội dung",
                    placeholder="Nhập nội dung chi tiết...",
                    height=150
                )
                
                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    status = st.selectbox(
                        "Trạng thái",
                        [
                            ('pending', '⏳ Đang chờ'),
                            ('in_progress', '🔄 Đang làm')
                        ],
                        format_func=lambda x: x[1]
                    )[0]
                with col2:
                    due_date = st.date_input(
                        "Hạn hoàn thành",
                        value=None,
                        help="Chọn ngày hạn hoàn thành (nếu có)"
                    )
                
                with col3:
                    submitted = st.form_submit_button(
                        "✅ Tạo ghi chú",
                        use_container_width=True,
                        type="primary"
                    )
                
                if submitted:
                    if not title:
                        st.error("Vui lòng nhập tiêu đề")
                    else:
                        note_data = {
                            'title': title,
                            'content': content,
                            'category': category,
                            'priority': priority,
                            'layer': layer,
                            'status': status,
                            'due_date': due_date.strftime('%Y-%m-%d') if due_date else None
                        }
                        result = NoteService.create_note(user_id, note_data)
                        if result['success']:
                            st.success(result['message'])
                            st.session_state['show_create_note'] = False
                            st.rerun()
                        else:
                            st.error(result['message'])
        st.divider()
    
    # Bộ lọc
    with st.expander("🔍 Bộ lọc nâng cao", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            filter_category = st.selectbox(
                "Loại",
                ["Tất cả", "Công việc", "Cá nhân", "Dự án", "Khẩn cấp", "Chung"],
                key="filter_category"
            )
        with col2:
            filter_priority = st.selectbox(
                "Mức độ ưu tiên",
                ["Tất cả", "Cực kỳ quan trọng", "Quan trọng", "Bình thường", "Thấp"],
                key="filter_priority"
            )
        with col3:
            filter_status = st.selectbox(
                "Trạng thái",
                ["Tất cả", "Đang chờ", "Đang làm", "Hoàn thành"],
                key="filter_status"
            )
        with col4:
            filter_layer = st.selectbox(
                "Lớp",
                ["Tất cả"] + [f"Lớp {i}" for i in range(1, 6)],
                key="filter_layer"
            )
    
    # Lấy danh sách ghi chú
    notes = NoteService.get_notes(user_id, role)
    
    # Áp dụng bộ lọc
    if notes:
        category_map = {
            'work': 'Công việc',
            'personal': 'Cá nhân',
            'project': 'Dự án',
            'urgent': 'Khẩn cấp',
            'general': 'Chung'
        }
        priority_map = {
            'critical': 'Cực kỳ quan trọng',
            'high': 'Quan trọng',
            'medium': 'Bình thường',
            'low': 'Thấp'
        }
        status_map = {
            'pending': 'Đang chờ',
            'in_progress': 'Đang làm',
            'done': 'Hoàn thành'
        }
        
        if filter_category != "Tất cả":
            notes = [n for n in notes if category_map.get(n['category']) == filter_category]
        if filter_priority != "Tất cả":
            notes = [n for n in notes if priority_map.get(n['priority']) == filter_priority]
        if filter_status != "Tất cả":
            notes = [n for n in notes if status_map.get(n['status']) == filter_status]
        if filter_layer != "Tất cả":
            layer_num = int(filter_layer.split()[1])
            notes = [n for n in notes if n['layer'] == layer_num]
    
    st.info(f"📌 Tổng số: {len(notes)} ghi chú")
    
    if not notes:
        st.warning("Không có ghi chú nào. Hãy tạo ghi chú đầu tiên!")
    else:
        # Tabs
        tab_names = ["📋 Tất cả", "⏳ Đang chờ", "🔄 Đang làm", "✅ Hoàn thành"]
        tabs = st.tabs(tab_names)
        
        with tabs[0]:
            for note in notes:
                # 1. Render cái card HTML (Đã sửa không lỗi)
                render_note_card(note, is_admin)
                
                # 2. Thanh điều khiển tác vụ nhỏ gọn nằm ngay dưới card
                col_btn1, col_btn2, col_btn3, _ = st.columns([1.5, 1, 1, 6])
                with col_btn1:
                    read_label = "Chuyển thành: Chưa đọc" if note['is_read'] else "Chuyển thành: Đã đọc"
                    btn_icon = "👁️ Đã đọc" if note['is_read'] else "🔔 Chưa đọc"
                    if st.button(btn_icon, key=f"read_{note['id']}", help=read_label, use_container_width=True):
                        result = NoteService.toggle_read_status(note['id'], user_id, note['is_read'])
                        if result['success']:
                            st.rerun()
                with col_btn2:
                    if st.button("✏️ Sửa", key=f"edit_{note['id']}", use_container_width=True):
                        st.session_state['editing_note'] = note
                        st.rerun()
                with col_btn3:
                    if st.button("🗑️ Xóa", key=f"delete_{note['id']}", use_container_width=True):
                        result = NoteService.delete_note(note['id'], user_id, role)
                        if result['success']:
                            st.success(result['message'])
                            st.rerun()
                        else:
                            st.error(result['message'])
                
                st.write("") # Tạo khoảng cách nhỏ giữa các Note
        
        with tabs[1]:
            pending_notes = [n for n in notes if n['status'] == 'pending']
            if pending_notes:
                for note in pending_notes:
                    render_note_card(note, is_admin)
            else:
                st.info("Không có ghi chú nào đang chờ")
        
        with tabs[2]:
            in_progress_notes = [n for n in notes if n['status'] == 'in_progress']
            if in_progress_notes:
                for note in in_progress_notes:
                    render_note_card(note, is_admin)
            else:
                st.info("Không có ghi chú nào đang làm")
        
        with tabs[3]:
            done_notes = [n for n in notes if n['status'] == 'done']
            if done_notes:
                for note in done_notes:
                    render_note_card(note, is_admin)
            else:
                st.info("Chưa có ghi chú nào hoàn thành")
    
    # Form sửa ghi chú
    if 'editing_note' in st.session_state:
        note = st.session_state['editing_note']
        with st.expander("✏️ Chỉnh sửa ghi chú", expanded=True):
            with st.form("edit_note_form"):
                col1, col2 = st.columns(2)
                with col1:
                    edit_title = st.text_input("Tiêu đề *", value=note['title'])
                    edit_category = st.selectbox(
                        "Loại",
                        [
                            ('work', '💼 Công việc'),
                            ('personal', '👤 Cá nhân'),
                            ('project', '📊 Dự án'),
                            ('urgent', '🚨 Khẩn cấp'),
                            ('general', '📝 Chung')
                        ],
                        format_func=lambda x: x[1],
                        index=[c[0] for c in [('work', ''), ('personal', ''), ('project', ''), ('urgent', ''), ('general', '')]].index(note['category'])
                    )[0]
                with col2:
                    edit_priority = st.selectbox(
                        "Mức độ ưu tiên",
                        [
                            ('critical', '🔴 Cực kỳ quan trọng'),
                            ('high', '🟠 Quan trọng'),
                            ('medium', '🟡 Bình thường'),
                            ('low', '🟢 Thấp')
                        ],
                        format_func=lambda x: x[1],
                        index=[c[0] for c in [('critical', ''), ('high', ''), ('medium', ''), ('low', '')]].index(note['priority'])
                    )[0]
                    edit_layer = st.selectbox(
                        "Lớp theo dõi",
                        [1, 2, 3, 4, 5],
                        format_func=lambda x: f"🌟 Lớp {x}",
                        index=note['layer'] - 1 if note['layer'] <= 5 else 0
                    )
                
                edit_content = st.text_area("Nội dung", value=note['content'] or '', height=150)
                
                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    edit_status = st.selectbox(
                        "Trạng thái",
                        [
                            ('pending', '⏳ Đang chờ'),
                            ('in_progress', '🔄 Đang làm'),
                            ('done', '✅ Hoàn thành')
                        ],
                        format_func=lambda x: x[1],
                        index=[c[0] for c in [('pending', ''), ('in_progress', ''), ('done', '')]].index(note['status'])
                    )[0]
                with col2:
                    edit_due_date = st.date_input(
                        "Hạn hoàn thành",
                        value=note['due_date'] if note['due_date'] else None
                    )
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 Cập nhật", use_container_width=True, type="primary"):
                        update_data = {
                            'title': edit_title,
                            'content': edit_content,
                            'category': edit_category,
                            'priority': edit_priority,
                            'layer': edit_layer,
                            'status': edit_status,
                            'due_date': edit_due_date.strftime('%Y-%m-%d') if edit_due_date else None
                        }
                        result = NoteService.update_note(note['id'], user_id, role, update_data)
                        if result['success']:
                            st.success(result['message'])
                            del st.session_state['editing_note']
                            st.rerun()
                        else:
                            st.error(result['message'])
                with col2:
                    if st.form_submit_button("❌ Hủy", use_container_width=True):
                        del st.session_state['editing_note']
                        st.rerun()