import streamlit as st
import pandas as pd
from datetime import datetime
from services.note_service import NoteService
from components.note_components import (
    render_notes_summary,
    render_quick_actions
)
import math

def calculate_countdown(due_date_str):
    """Tính toán số ngày đếm ngược đến hạn"""
    if not due_date_str:
        return "♾️ Không giới hạn"
    try:
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        today = datetime.now().date()
        delta = (due_date - today).days
        
        if delta < 0:
            return f"🚨 Quá hạn {abs(delta)} ngày"
        elif delta == 0:
            return "🔥 Hôm nay!"
        else:
            return f"⏳ Còn {delta} ngày"
    except Exception:
        return "⚠️ Lỗi định dạng ngày"

def show_notes_page():
    """Trang quản lý ghi chú tối ưu giao diện Bảng & Tích hợp tính năng cao cấp"""
    
    if 'username' not in st.session_state:
        st.warning("Vui lòng đăng nhập để xem ghi chú")
        return
    
    user_id = st.session_state.get('user_id')
    if not user_id:
        st.error("Không tìm thấy ID người dùng. Vui lòng đăng nhập lại.")
        return
        
    role = st.session_state.get('role', '')
    is_admin = role == "ADMIN"
    
    st.title("📋 Quản lý Ghi chú")
    st.caption("Hệ thống quản lý, theo dõi tiến độ và đếm ngược thời hạn ghi chú thông minh")
    st.divider()
    
    # 📊 Thống kê tổng quan
    stats = NoteService.get_statistics(user_id, role)
    render_notes_summary(stats)
    st.divider()
    
    # ⚡ Thao tác nhanh
    render_quick_actions()
    st.divider()
    
    # 📝 Form tạo ghi chú mới
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
                    "Nội dung (Hỗ trợ định dạng **Markdown**)",
                    placeholder="Nhập nội dung... Bạn có thể dùng các định dạng Markdown như **in đậm**, *in nghiêng*, - gạch đầu dòng...",
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
                        help="Chọn ngày hạn hoàn thành để kích hoạt bộ đếm ngược"
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
    
    # 🔍 TÍNH NĂNG 1: TÌM KIẾM NHANH & BỘ LỌC ĐỘNG
    st.markdown("### 🛠️ Bộ lọc & Tìm kiếm")
    search_query = st.text_input("🔍 Tìm kiếm nhanh", placeholder="Nhập tiêu đề hoặc nội dung ghi chú cần tìm...")
    
    with st.expander("⚙️ Bộ lọc nâng cao", expanded=False):
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
    
    # Đọc dữ liệu gốc từ Service
    raw_notes = NoteService.get_notes(user_id, role)
    
    # Khởi tạo danh sách xử lý dữ liệu bảng
    processed_notes = []
    
    if raw_notes:
        category_map = {'work': 'Công việc', 'personal': 'Cá nhân', 'project': 'Dự án', 'urgent': 'Khẩn cấp', 'general': 'Chung'}
        priority_map = {'critical': 'Cực kỳ quan trọng', 'high': 'Quan trọng', 'medium': 'Bình thường', 'low': 'Thấp'}
        status_map = {'pending': 'Đang chờ', 'in_progress': 'Đang làm', 'done': 'Hoàn thành'}
        
        # Tiến hành lọc dữ liệu dựa trên Search Bar và các Selectbox
        for n in raw_notes:
            cat_vn = category_map.get(n['category'], 'Chung')
            prio_vn = priority_map.get(n['priority'], 'Bình thường')
            stat_vn = status_map.get(n['status'], 'Đang chờ')
            
            # Khớp điều kiện bộ lọc nâng cao
            if filter_category != "Tất cả" and cat_vn != filter_category: continue
            if filter_priority != "Tất cả" and prio_vn != filter_priority: continue
            if filter_status != "Tất cả" and stat_vn != filter_status: continue
            if filter_layer != "Tất cả" and n['layer'] != int(filter_layer.split()[1]): continue
            
            # Khớp điều kiện ô Tìm kiếm nhanh
            if search_query:
                q = search_query.lower()
                in_title = q in (n.get('title') or '').lower()
                in_content = q in (n.get('content') or '').lower()
                if not (in_title or in_content):
                    continue
            
            # TÍNH NĂNG 3: Tính toán đếm ngược thời hạn
            countdown = calculate_countdown(n.get('due_date'))
            
            processed_notes.append({
                'ID': n['id'],
                'Tiêu đề': n['title'],
                'Loại': cat_vn,
                'Độ ưu tiên': prio_vn,
                'Lớp': f"Lớp {n['layer']}",
                'Trạng thái': stat_vn,
                'Đọc': "👁️ Đã đọc" if n.get('is_read') else "🔔 Chưa đọc",
                'Hạn hoàn thành': n['due_date'] if n['due_date'] else "Không có",
                'Đếm ngược': countdown,
                '_raw_data': n  # Lưu giữ data gốc phục vụ cho tương tác xem/sửa/xóa
            })

    st.info(f"📌 Tìm thấy: {len(processed_notes)} ghi chú phù hợp")
    
    if not processed_notes:
        st.warning("Không có ghi chú nào thỏa mãn điều kiện lọc.")
        return

    # Convert thành DataFrame để hiển thị cấu trúc bảng
    df = pd.DataFrame(processed_notes)
    
    # Cấu hình hiển thị bảng đẹp mắt bằng st.dataframe mới của Streamlit
    st.markdown("### 📊 Danh sách Ghi chú (Table View)")
    st.caption("💡 Mẹo: Nhấp vào ô tròn đầu dòng của bảng để chọn xem chi tiết, sửa hoặc xóa ghi chú đó.")
    
    # Ẩn cột id và dữ liệu thô khỏi giao diện bảng
    display_df = df.drop(columns=['ID', '_raw_data'])
    
    # =========================================================================
    # ĐOẠN MỐC TRÊN: (Giữ nguyên code cũ của bạn)
    # Thường là đoạn xử lý tìm kiếm hoặc chuẩn bị dữ liệu display_df, ví dụ:
    # display_df = df[df['title'].str.contains(search_query, ...)]
    # =========================================================================


    # ⬇️⬇️⬇️ BẮT ĐẦU CHÈN TOÀN BỘ ĐOẠN PHÂN TRANG VÀO ĐÂY (THAY THẾ CHO st.dataframe CŨ) ⬇️⬇️⬇️
    
    ITEMS_PER_PAGE = 10 # Số dòng mỗi trang
    
    if "note_page_number" not in st.session_state:
        st.session_state["note_page_number"] = 1
        
    total_items = len(display_df)
    
    if total_items > 0:
        total_pages = math.ceil(total_items / ITEMS_PER_PAGE)
        
        if st.session_state["note_page_number"] > total_pages:
            st.session_state["note_page_number"] = total_pages
        if st.session_state["note_page_number"] < 1:
            st.session_state["note_page_number"] = 1
            
        current_page = st.session_state["note_page_number"]
        
        start_idx = (current_page - 1) * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        page_df = display_df.iloc[start_idx:end_idx]
        
        # Hiển thị bảng đã được cắt theo trang
        selected_rows = st.dataframe(
            page_df,             # <-- Đã đổi từ display_df thành page_df
            use_container_width=True,
            on_select="rerun",
            selection_mode="single-row"
        )
        
        # Thanh điều hướng nút bấm (Trước / Sau)
        st.write("") 
        col_info, col_prev, col_next = st.columns([3, 1, 1])
        
        with col_info:
            actual_end = min(end_idx, total_items)
            st.caption(f"Hiển thị **{start_idx + 1}-{actual_end}** trong tổng số **{total_items}** ghi chú (Trang {current_page}/{total_pages})")
            
        with col_prev:
            if st.button("⬅️ Trang trước", use_container_width=True, disabled=(current_page == 1)):
                st.session_state["note_page_number"] -= 1
                st.rerun()
                
        with col_next:
            if st.button("Trang sau ➡️", use_container_width=True, disabled=(current_page == total_pages)):
                st.session_state["note_page_number"] += 1
                st.rerun()
                
    else:
        st.info("Không tìm thấy ghi chú nào phù hợp.")
        selected_rows = None  # Đảm bảo biến selected_rows vẫn tồn tại nếu bảng trống
        
    # ⬆️⬆️⬆️ KẾT THÚC ĐOẠN CHÈN MỚI ⬆️⬆️⬆️


    # =========================================================================
    # ĐOẠN MỐC DƯỚI: (Giữ nguyên code cũ của bạn)
    # Thường là đoạn xử lý logic khi người dùng click chọn dòng trên bảng, ví dụ:
    # if selected_rows and len(selected_rows["selection"]["rows"]) > 0:
    #     ... xử lý mở form Sửa/Xóa ...
    # =========================================================================
    # Kiểm tra xem người dùng có đang click chọn dòng nào trên bảng không
    selected_index = selected_rows.get("selection", {}).get("rows", [])
    
    if selected_index:
        actual_index = selected_index[0]
        selected_note_raw = df.iloc[actual_index]['_raw_data']
        
        st.write("")
        st.markdown("---")
        
        # Tạo khu vực hiển thị chi tiết mượt mà theo tab bên dưới bảng
        detail_col, action_col = st.columns([7, 3])
        
        with detail_col:
            st.markdown(f"### 🔍 Chi tiết: {selected_note_raw['title']}")
            
            # TÍNH NĂNG 2: Render nội dung Markdown trực quan
            st.markdown("**📝 Nội dung ghi chú:**")
            if selected_note_raw['content']:
                st.info(selected_note_raw['content'])
            else:
                st.text("Ghi chú này không có nội dung văn bản.")
                
        with action_col:
            st.markdown("**⚡ Thao tác xử lý**")
            
            # Các nút bấm tương tác nhanh với bản ghi được chọn
            read_label = "Đánh dấu Chưa đọc" if selected_note_raw['is_read'] else "Đánh dấu Đã đọc"
            btn_icon = "👁️ Đã đọc" if selected_note_raw['is_read'] else "🔔 Chưa đọc"
            
            if st.button(btn_icon, key="tbl_read", help=read_label, use_container_width=True):
                result = NoteService.toggle_read_status(selected_note_raw['id'], user_id, selected_note_raw['is_read'])
                if result['success']: st.rerun()
                    
            if st.button("✏️ Chỉnh sửa", key="tbl_edit", use_container_width=True):
                st.session_state['editing_note'] = selected_note_raw
                st.rerun()
                
            if st.button("🗑️ Xóa ghi chú", key="tbl_delete", type="primary", use_container_width=True):
                result = NoteService.delete_note(selected_note_raw['id'], user_id, role)
                if result['success']:
                    st.success(result['message'])
                    st.rerun()
                else:
                    st.error(result['message'])
    
    # ✏️ Form chỉnh sửa ghi chú khi có hành động Click nút Sửa
    if 'editing_note' in st.session_state:
        note = st.session_state['editing_note']
        st.write("")
        st.markdown("---")
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
                        value=datetime.strptime(note['due_date'], '%Y-%m-%d').date() if note['due_date'] else None
                    )
                
                col_b1, col_b2 = st.columns(2)
                with col_b1:
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
                with col_b2:
                    if st.form_submit_button("❌ Hủy", use_container_width=True):
                        del st.session_state['editing_note']
                        st.rerun()