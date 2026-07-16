import streamlit as st
import pandas as pd
import os
import shutil
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
from database.pg_database import query_pg_to_dataframe, execute_pg_query

# =========================================================================
# 📂 CẤU HÌNH THƯ MỤC LƯU TRỮ (SERVER HOẶC MẠNG LAN)
# =========================================================================
# - Cách 1: Lưu cục bộ trên máy chủ (máy của bạn đang chạy Streamlit):
BASE_ARCHIVE_DIR = "KHO_LUU_TRU_KE_TOAN"

# - Cách 2 (Nếu muốn lưu vào ổ cứng chung trong mạng LAN):
# Hãy uncomment dòng dưới và thay bằng IP/Đường dẫn thư mục chia sẻ của bạn
# BASE_ARCHIVE_DIR = r"\\192.168.1.100\SharedFolder\KHO_LUU_TRU_KE_TOAN"

# Tạo thư mục gốc nếu chưa tồn tại
if not os.path.exists(BASE_ARCHIVE_DIR):
    try:
        os.makedirs(BASE_ARCHIVE_DIR, exist_ok=True)
    except Exception as e:
        st.error(f"⚠️ Không thể khởi tạo thư mục lưu trữ: {str(e)}. Vui lòng kiểm tra quyền ghi.")

# Hàm hỗ trợ dọn dẹp thư mục rỗng khi xóa file để tránh rác máy chủ
def delete_empty_parent_folders(file_path, base_limit_dir):
    parent_dir = os.path.dirname(file_path)
    while parent_dir and os.path.abspath(parent_dir) != os.path.abspath(base_limit_dir):
        if os.path.exists(parent_dir) and len(os.listdir(parent_dir)) == 0:
            try:
                os.rmdir(parent_dir)
                parent_dir = os.path.dirname(parent_dir)
            except Exception:
                break
        else:
            break

def show_document_archive_page():
    # =========================================================================
    # 🔐 PHÂN QUYỀN TRUY CẬP
    # =========================================================================
    role = st.session_state.get("role")
    username = st.session_state.get("username", "Unknown")
    
    if role not in ["ADMIN", "ACCOUNTANT"]:
        st.error("⛔ Bạn không có quyền truy cập vào trang Lưu Trữ Hồ Sơ Kế Toán này!")
        st.stop()
        
    st.title("🗄️ Kho Lưu Trữ & Tra Cứu Hồ Sơ Kế Toán")
    st.markdown("---")

    # =========================================================================
    # 📊 TẢI DỮ LIỆU TỪ DATABASE (Đã fix lỗi hiển thị ngày tháng [object Object])
    # =========================================================================
    # Lấy danh sách chờ file (từ trang kế toán xác nhận sang)
    waiting_query = """
        SELECT id, order_number, customer_name, customer_code, 
               document_type, file_type, file_path, archive_date, created_by, note
        FROM document_archives
        WHERE file_type = 'CHỜ FILE'
        ORDER BY created_at DESC
    """
    df_waiting = query_pg_to_dataframe(waiting_query)
    
    # Ép kiểu ngày tháng thành chuỗi text đẹp đẽ để tránh lỗi [object Object] của AgGrid
    if not df_waiting.empty and "archive_date" in df_waiting.columns:
        df_waiting["archive_date"] = pd.to_datetime(df_waiting["archive_date"]).dt.strftime('%Y-%m-%d %H:%M:%S')

    # Lấy danh sách hồ sơ chính thức (đã có file thực tế)
    archived_query = """
        SELECT id, order_number, customer_name, customer_code, 
               document_type, file_type, file_path, archive_date, created_by, note
        FROM document_archives
        WHERE file_type != 'CHỜ FILE'
        ORDER BY created_at DESC
    """
    df_archived = query_pg_to_dataframe(archived_query)
    
    # Ép kiểu ngày tháng danh sách chính thức thành chuỗi text
    if not df_archived.empty and "archive_date" in df_archived.columns:
        df_archived["archive_date"] = pd.to_datetime(df_archived["archive_date"]).dt.strftime('%Y-%m-%d %H:%M:%S')

    # =========================================================================
    # 🏗️ PHẦN 1: GIAO DIỆN NHẬP & HOÀN THIỆN HỒ SƠ (CHIA THÀNH 2 TAB RIÊNG BIỆT)
    # =========================================================================
    st.markdown("## 📥 Tiếp Nhận & Lưu Trữ Hồ Sơ")
    tab_auto, tab_manual = st.tabs([
        "⚡ Hồ Sơ Chờ Hoàn Thiện File (Từ Kế Toán)", 
        "✍️ Khởi Tạo Lưu Trữ Thủ Công"
    ])

    # -------------------------------------------------------------------------
    # TAB A: XỬ LÝ ĐỒNG BỘ TỪ KẾ TOÁN (Tự động điền dữ liệu khi click dòng)
    # -------------------------------------------------------------------------
    with tab_auto:
        st.markdown("### 1. Danh sách hồ sơ kế toán đã ký nhận (Chờ File thực tế)")
        
        selected_waiting_row = None
        
        if df_waiting.empty:
            st.info("🎉 Hiện tại không có hồ sơ nào đang chờ bổ sung file thực tế!")
        else:
            # Chuẩn bị dữ liệu hiển thị AgGrid Chờ File
            waiting_grid_data = df_waiting.copy()
            waiting_grid_data.columns = [
                "ID", "Mã Đơn", "Tên Khách Hàng", "Mã Khách Hàng", 
                "Loại Hồ Sơ", "Định Dạng", "Đường Dẫn Vật Lý", "Ngày Chuyển Sang", "Người Chuyển", "Ghi Chú"
            ]
            
            gb_w = GridOptionsBuilder.from_dataframe(waiting_grid_data)
            gb_w.configure_pagination(paginationAutoPageSize=False, paginationPageSize=5)
            gb_w.configure_default_column(resizable=True, sortable=True, filter=True)
            gb_w.configure_selection(selection_mode="single", use_checkbox=True)
            gridOptions_w = gb_w.build()
            
            grid_waiting_resp = AgGrid(
                waiting_grid_data,
                gridOptions=gridOptions_w,
                height=220,
                width='100%',
                data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
                update_mode=GridUpdateMode.SELECTION_CHANGED,
                theme="streamlit",
                key="waiting_archive_grid"
            )
            
            # Xử lý lấy dòng được chọn từ bảng Chờ File
            sel_rows_w = grid_waiting_resp.get("selected_rows", [])
            if sel_rows_w is not None and len(sel_rows_w) > 0:
                if isinstance(sel_rows_w, pd.DataFrame):
                    selected_waiting_row = sel_rows_w.iloc[0].to_dict()
                elif isinstance(sel_rows_w, list):
                    first_item = sel_rows_w[0]
                    selected_waiting_row = first_item.get("data", first_item) if isinstance(first_item, dict) else getattr(first_item, "data", first_item)

        st.markdown("---")
        st.markdown("### 2. Form Hoàn Thiện & Cất Kho")
        
        # Nếu người dùng chọn 1 dòng trên bảng chờ file, tự động trích xuất thông tin đổ vào Form
        if selected_waiting_row:
            wait_id = int(selected_waiting_row["ID"])
            wait_order = str(selected_waiting_row["Mã Đơn"])
            wait_cust_name = str(selected_waiting_row["Tên Khách Hàng"])
            wait_cust_code = str(selected_waiting_row["Mã Khách Hàng"])
            wait_note = str(selected_waiting_row["Ghi Chú"])
            
            st.success(f"🎯 Đang xử lý hồ sơ ID `{wait_id}` - Đơn hàng: **{wait_order}** của KH: **{wait_cust_name}**")
            
            with st.form("auto_complete_form"):
                col_a1, col_a2 = st.columns(2)
                with col_a1:
                    st.text_input("Mã Đơn Hàng (Tự Động):", value=wait_order, disabled=True)
                    st.text_input("Tên Khách Hàng (Tự Động):", value=wait_cust_name, disabled=True)
                    st.text_input("Mã Khách Hàng (Tự Động):", value=wait_cust_code, disabled=True)
                with col_a2:
                    auto_doc_type = st.selectbox(
                        "Chọn Loại Hồ Sơ Thực Tế *:", 
                        ["Hóa Đơn Đỏ", "Hợp Đồng Kinh Tế", "Tờ Khai Hải Quan", "Báo Cáo Tài Chính", "Khác..."],
                        key="auto_doc_type_select"
                    )
                    if auto_doc_type == "Khác...":
                        auto_doc_type = st.text_input("Nhập Loại Hồ Sơ Khác *:", key="auto_doc_type_other")
                        
                    auto_uploaded_file = st.file_uploader("Đính kèm File hồ sơ thực tế *:", type=["pdf", "xlsx", "xls", "docx", "doc", "jpg", "png"], key="auto_file")
                    auto_note = st.text_area("Ghi chú bổ sung (nếu có):", value=wait_note, key="auto_note_text")
                
                auto_submit = st.form_submit_button("📁 Hoàn Tất Cất Kho Hồ Sơ", use_container_width=True, type="primary")
                
                if auto_submit:
                    if not auto_uploaded_file:
                        st.error("❌ Bạn chưa tải lên file đính kèm thực tế!")
                    elif not auto_doc_type or auto_doc_type == "Khác...":
                        st.error("❌ Vui lòng điền/chọn loại hồ sơ hợp lệ!")
                    else:
                        file_ext = os.path.splitext(auto_uploaded_file.name)[1].lower().replace(".", "")
                        folder_name = f"{wait_cust_name}_{wait_order}".replace(" ", "_").replace("/", "-")
                        
                        dest_dir = os.path.join(BASE_ARCHIVE_DIR, folder_name, auto_doc_type.replace(" ", "_").replace("/", "-"), file_ext.upper())
                        os.makedirs(dest_dir, exist_ok=True)
                        final_path = os.path.join(dest_dir, auto_uploaded_file.name)
                        
                        try:
                            # Ghi file vật lý lên Server
                            with open(final_path, "wb") as f:
                                f.write(auto_uploaded_file.getbuffer())
                            
                            # Cập nhật thông tin vào DB, xóa bỏ trạng thái CHỜ FILE
                            update_query = """
                                UPDATE document_archives
                                SET document_type = %s,
                                    file_type = %s,
                                    file_path = %s,
                                    note = %s,
                                    created_by = %s,
                                    archive_date = CURRENT_TIMESTAMP,
                                    created_at = CURRENT_TIMESTAMP
                                WHERE id = %s
                            """
                            execute_pg_query(update_query, (
                                auto_doc_type,
                                file_ext.upper(),
                                final_path,
                                f"[Bổ sung file thực tế] {auto_note}" if auto_note else "[Bổ sung file thực tế]",
                                username,
                                wait_id
                            ))
                            st.success(f"🎉 Đã hoàn tất cập nhật File thực tế và lưu trữ thành công cho đơn `{wait_order}`!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Lỗi ghi nhận file: {str(e)}")
        else:
            st.info("💡 Vui lòng tích chọn một hồ sơ chờ trên bảng danh sách ở trên để hệ thống tự động điền thông tin vào form!")

    # -------------------------------------------------------------------------
    # TAB B: KHỞI TẠO LƯU TRỮ THỦ CÔNG (Tự nhập hoàn toàn)
    # -------------------------------------------------------------------------
    with tab_manual:
        st.markdown("### ✍️ Nhập Mới Hồ Sơ Ngoài Luồng Hệ Thống")
        
        with st.form("manual_archive_form"):
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                manual_order = st.text_input("Mã Đơn Hàng *:", placeholder="Ví dụ: ORD9999", key="man_order")
                manual_cust_name = st.text_input("Tên Khách Hàng *:", placeholder="Ví dụ: Công ty Hoàng Gia", key="man_cust_name")
                manual_cust_code = st.text_input("Mã Khách Hàng *:", placeholder="Ví dụ: KH00999", key="man_cust_code")
            with col_m2:
                manual_doc_type = st.selectbox(
                    "Loại Hồ Sơ *:", 
                    ["Hóa Đơn Đỏ", "Hợp Đồng Kinh Tế", "Tờ Khai Hải Quan", "Báo Cáo Tài Chính", "Khác..."],
                    key="man_doc_type"
                )
                if manual_doc_type == "Khác...":
                    manual_doc_type = st.text_input("Nhập Loại Hồ Sơ Khác *:", key="man_doc_type_other")
                    
                manual_file = st.file_uploader("Đính kèm File hồ sơ *:", type=["pdf", "xlsx", "xls", "docx", "doc", "jpg", "png"], key="man_file")
                manual_note = st.text_area("Ghi chú:", placeholder="Ví dụ: Lưu trữ thủ công nội bộ...", key="man_note")
                
            manual_submit = st.form_submit_button("📁 Lưu Kho Thủ Công", use_container_width=True)
            
            if manual_submit:
                man_order_clean = manual_order.strip() if manual_order else ""
                man_name_clean = manual_cust_name.strip() if manual_cust_name else ""
                man_code_clean = manual_cust_code.strip() if manual_cust_code else ""
                man_type_clean = manual_doc_type.strip() if manual_doc_type else ""
                
                if not man_order_clean:
                    st.error("❌ Bạn chưa điền Mã Đơn Hàng!")
                elif not man_name_clean:
                    st.error("❌ Bạn chưa điền Tên Khách Hàng!")
                elif not man_code_clean:
                    st.error("❌ Bạn chưa điền Mã Khách Hàng!")
                elif not man_type_clean or man_type_clean == "Khác...":
                    st.error("❌ Bạn chưa chọn hoặc nhập Loại Hồ Sơ!")
                elif not manual_file:
                    st.error("❌ Bạn chưa đính kèm File hồ sơ thực tế!")
                else:
                    file_ext = os.path.splitext(manual_file.name)[1].lower().replace(".", "")
                    folder_name = f"{man_name_clean}_{man_order_clean}".replace(" ", "_").replace("/", "-")
                    
                    dest_dir = os.path.join(BASE_ARCHIVE_DIR, folder_name, man_type_clean.replace(" ", "_").replace("/", "-"), file_ext.upper())
                    os.makedirs(dest_dir, exist_ok=True)
                    final_path = os.path.join(dest_dir, manual_file.name)
                    
                    try:
                        # Ghi file vật lý lên Server
                        with open(final_path, "wb") as f:
                            f.write(manual_file.getbuffer())
                        
                        # Ghi nhận bản ghi chính thức vào DB (Đã lưu đầy đủ tệp đính kèm)
                        insert_query = """
                            INSERT INTO document_archives 
                            (order_number, customer_name, customer_code, document_type, file_type, file_path, note, created_by, archive_date)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                        """
                        execute_pg_query(insert_query, (
                            man_order_clean,
                            man_name_clean,
                            man_code_clean,
                            man_type_clean,
                            file_ext.upper(),
                            final_path,
                            manual_note,
                            username
                        ))
                        st.success(f"🎉 Đã thêm mới và lưu trữ thành công hồ sơ vào kho: `{final_path}`")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Đã xảy ra lỗi khi ghi nhận file: {str(e)}")

    # =========================================================================
    # 📊 PHẦN 2: DANH SÁCH TOÀN BỘ HỒ SƠ ĐÃ LƯU TRONG KHO CHÍNH THỨC
    # =========================================================================
    st.markdown("---")
    st.markdown("## 📜 Danh Sách Hồ Sơ Đã Lưu Trữ")
    
    search_keyword = st.text_input("🔍 Tìm kiếm nhanh hồ sơ trong kho:", value="", key="archive_filter_quick")
    
    if df_archived.empty:
        st.info("Hiện tại chưa có hồ sơ lưu chính thức nào trong kho.")
    else:
        # Áp dụng bộ lọc tìm kiếm
        if search_keyword:
            kw = search_keyword.lower()
            df_archived = df_archived[
                df_archived.astype(str).apply(lambda col: col.str.lower()).apply(lambda col: col.str.contains(kw, na=False)).any(axis=1)
            ]

        grid_data = df_archived.copy()
        grid_data.columns = [
            "ID", "Mã Đơn", "Tên Khách Hàng", "Mã Khách Hàng", 
            "Loại Hồ Sơ", "Định Dạng", "Đường Dẫn Vật Lý", "Ngày Lưu Kho", "Người Lưu", "Ghi Chú"
        ]

        # Cấu hình hiển thị AgGrid danh sách lưu trữ
        gb = GridOptionsBuilder.from_dataframe(grid_data)
        gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=10)
        gb.configure_default_column(resizable=True, sortable=True, filter=True)
        gb.configure_selection(selection_mode="single", use_checkbox=True) # Chỉ cho chọn 1 dòng tại một thời điểm
        
        grid_options_extra = {
            "enableCellTextSelection": True,
            "ensureDomOrder": True,
        }
        gb.configure_grid_options(**grid_options_extra)
        gridOptions = gb.build()

        grid_response = AgGrid(
            grid_data,
            gridOptions=gridOptions,
            height=350,
            width='100%',
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            theme="streamlit",
            key="archive_grid_viewer"
        )

        selected_rows = grid_response.get("selected_rows", [])
        
        # Xử lý làm sạch dòng được chọn
        row_to_process = None
        if selected_rows is not None:
            if isinstance(selected_rows, pd.DataFrame) and not selected_rows.empty:
                row_raw = selected_rows.iloc[0].to_dict()
            elif isinstance(selected_rows, list) and len(selected_rows) > 0:
                first_item = selected_rows[0]
                if isinstance(first_item, dict):
                    row_raw = first_item.get("data", first_item)
                else:
                    row_raw = getattr(first_item, "data", first_item)
            else:
                row_raw = None

            if row_raw and isinstance(row_raw, dict):
                row_to_process = {}
                for k, v in row_raw.items():
                    if not str(k).startswith('_'):
                        if isinstance(v, dict):
                            row_to_process[k] = v.get("value", str(v))
                        else:
                            row_to_process[k] = v

        # =========================================================================
        # 🎮 PHẦN 3: KHU VỰC THAO TÁC FILE (CHỈ XUẤT HIỆN KHI CÓ DÒNG ĐƯỢC CHỌN)
        # =========================================================================
        if row_to_process is not None:
            selected_id = int(row_to_process["ID"])
            selected_file_path = str(row_to_process["Đường Dẫn Vật Lý"])
            selected_order_num = str(row_to_process["Mã Đơn"])
            
            st.markdown("---")
            st.warning(f"🎯 Đang chọn hồ sơ ID: **{selected_id}** (Mã Đơn: **{selected_order_num}**). Vui lòng chọn hành động bên dưới:")
            
            col_action1, col_action2 = st.columns(2)
            
            # --- HÀNH ĐỘNG 1: DOWNLOAD FILE VỀ MÁY KHÁCH ---
            with col_action1:
                if selected_file_path and selected_file_path not in ["Chưa tải lên", "CHỜ FILE"] and os.path.exists(selected_file_path):
                    try:
                        file_name_only = os.path.basename(selected_file_path)
                        
                        # Sử dụng nút thường, IDM sẽ không thể tự bắt link khi click dòng nữa!
                        if st.button(f"📥 Chuẩn Bị Tải File ({file_name_only})", use_container_width=True, key=f"prepare_dl_{selected_id}"):
                            with open(selected_file_path, "rb") as file_bytes:
                                btn_data = file_bytes.read()
                            
                            # Nút download thực sự chỉ xuất hiện SAU KHI người dùng chủ động click nút chuẩn bị
                            st.download_button(
                                label="➔ BẤM VÀO ĐÂY ĐỂ LƯU FILE VỀ MÁY",
                                data=btn_data,
                                file_name=file_name_only,
                                mime="application/octet-stream",
                                use_container_width=True,
                                key=f"real_download_btn_{selected_id}"
                            )
                    except Exception as ex_load:
                        st.error(f"Không thể tải file: {str(ex_load)}")
                else:
                    st.info("ℹ️ Không tìm thấy file vật lý của bản ghi này trên máy chủ.")
            # --- HÀNH ĐỘNG 2: XÓA HỒ SƠ KHỎI KHO (Cần phân quyền Admin) ---
            with col_action2:
                confirm_delete = st.button("🗑️ Xác Nhận Xóa Bản Ghi & File", type="primary", use_container_width=True, key=f"del_btn_{selected_id}")
                
                if confirm_delete:
                    # 1. Thực hiện xóa file vật lý trên máy chủ
                    if selected_file_path and selected_file_path not in ["Chưa tải lên", "CHỜ FILE"] and os.path.exists(selected_file_path):
                        try:
                            os.remove(selected_file_path)
                            delete_empty_parent_folders(selected_file_path, BASE_ARCHIVE_DIR)
                        except Exception as ex_file:
                            st.warning(f"Lưu ý: Không thể xóa file vật lý (có thể do lỗi phân quyền ổ đĩa) nhưng sẽ tiếp tục xóa bản ghi trong DB. Chi tiết: {str(ex_file)}")

                    # 2. Xóa bản ghi trong PostgreSQL
                    delete_query = "DELETE FROM document_archives WHERE id = %s"
                    execute_pg_query(delete_query, (selected_id,))
                    
                    st.success("🎉 Đã dọn dẹp file vật lý và xóa bỏ hồ sơ khỏi kho dữ liệu thành công!")
                    st.rerun()