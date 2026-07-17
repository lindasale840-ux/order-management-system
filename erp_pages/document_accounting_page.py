import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
from repositories.document_accounting_repository import DocumentAccountingRepository
from services.document_accounting_service import DocumentAccountingService # Giả định service truyền username vào repo
from components.aggrid_table import render_aggrid 
from utils.data_permission import filter_by_sale_owner
from utils.auth_guard import require_editor
import numpy as np

def show_document_accounting_page():
    require_editor()
    
    st.title("📑 Điều Phối & Bàn Giao Hồ Sơ Kế Toán")
    role = st.session_state.get("role")
    username = st.session_state.get("username", "Unknown")
    
    # 1. Lấy dữ liệu ban đầu
    all_history_df = DocumentAccountingRepository.get_all_accounting_history()
    if all_history_df.empty:
        filtered_history_df = pd.DataFrame(columns=[
            "id", "document_tracking_id", "order_number", "sent_to_accounting_date", 
            "accounting_received_date", "is_received_by_accounting", "note", 
            "sale_owner", "created_by", "customer_name", "client_received_date"
        ])
    else:
        filtered_history_df = filter_by_sale_owner(all_history_df.copy())

    pending_df = DocumentAccountingRepository.get_pending_send_to_accounting()
    pending_df = filter_by_sale_owner(pending_df)
    if st.session_state["role"] in ["ADMIN", "SALE", "ASSISTANT"]:
        # =========================================================================
        # 🔍 BỘ LỌC TỔNG THÔNG MINH
        # =========================================================================
        st.markdown("### 🔍 Bộ Lọc Tìm Kiếm Nhanh")
        search_keyword = st.text_input("Gõ từ khóa để lọc nhanh trên cả 2 bảng (Mã đơn, Tên khách hàng...):", value="", key="main_search_filter")

        # -------------------------------------------------------------------------
        # CHỖ THỨ 1: PHẦN GỬI NGOÀI LUỒNG / CẬP NHẬT GỬI LẠI (THÔNG MINH)
        # -------------------------------------------------------------------------
        st.markdown("---")
        st.subheader("⚡ Chỗ 1: Gửi Hồ Sơ Ngoài Luồng / Sửa Đổi Gửi Lại Hồ Sơ")
        with st.form("direct_accounting_send_form_v3"):
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                direct_order_num = st.text_input("Nhập Mã Đơn Hàng:", placeholder="Ví dụ: ORD9999")
                direct_sent_date = st.date_input("Ngày thực tế gửi Kế toán:", value=pd.Timestamp.today().date())
            with col_d2:
                direct_note = st.text_area("Ghi chú nội dung bàn giao / Lý do gửi lại:", placeholder="Nhập ghi chú chi tiết hoặc sửa đổi nội dung tại đây...")
            
            submit_direct = st.form_submit_button("🚀 Xác nhận Gửi / Cập nhật gửi lại hồ sơ cho Kế toán", use_container_width=True)
            if submit_direct:
                order_clean = direct_order_num.strip()
                if not order_clean:
                    st.error("Vui lòng nhập Mã Đơn Hàng!")
                else:
                    # KIỂM TRA LOGIC THÔNG MINH: Đơn này đã từng tồn tại trong luồng xử lý và đang bị kẹt chưa duyệt không?
                    from database.pg_database import query_pg_to_dataframe, execute_pg_query # Đảm bảo import để check trực tiếp nhanh
                    check_query = "SELECT id FROM document_accounting_flows WHERE order_number = %s AND is_received_by_accounting = FALSE"
                    df_check = query_pg_to_dataframe(check_query, (order_clean,))
                    
                    if not df_check.empty:
                        # Tình huống: Đơn đang bị kẹt (do Điều phối hoàn tác hoặc Kế toán từ chối/hoàn tác) -> Chuyển thành hành động CẬP NHẬT để gửi lại
                        existing_flow_id = int(df_check.iloc[0]["id"])
                        update_query = """
                            UPDATE document_accounting_flows 
                            SET sent_to_accounting_date = %s,
                                note = %s,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """
                        execute_pg_query(update_query, (direct_sent_date, f"[Gửi lại] {direct_note}", existing_flow_id))
                        # Ghi nhận log cập nhật gửi lại
                        DocumentAccountingRepository.write_action_log(order_clean, "RESEND", username, f"Cập nhật dữ liệu và gửi lại hồ sơ. Ghi chú mới: {direct_note}")
                        st.success(f"♻️ Đã cập nhật thông tin và tái gửi lại đơn ngoài luồng {order_clean} sang cho Kế toán thành công!")
                    else:
                        # Tình huống: Đơn hoàn toàn mới -> Gọi hàm chèn mới gốc như cũ
                        DocumentAccountingRepository.add_direct_accounting_flow(order_clean, direct_sent_date, direct_note, username)
                        st.success(f"🚀 Đã tạo luồng gửi mới đơn ngoài luồng {order_clean} sang Kế toán thành công!")
                        
                    st.rerun()

        # -------------------------------------------------------------------------
        # CHỖ THỨ 2: DANH SÁCH ĐƠN TỰ ĐỘNG TỪ DOCUMENT TRACKING (GIỮ NGUYÊN LUỒNG CŨ)
        # -------------------------------------------------------------------------
        st.markdown("---")
        st.subheader("📥 Chỗ 2: Danh Sách Đơn Chờ Gửi Kế Toán (Từ Luồng Nhận Hồ Sơ)")
        
        overdue_filter_pending = st.selectbox(
            "Lọc theo thời gian trễ hạn (Chờ gửi):",
            ["Tất cả đơn chờ gửi", "🚨 Chỉ đơn quá hạn (≥ 3 ngày)", "🟢 Chỉ đơn trong hạn (< 3 ngày)"],
            index=0,
            key="pending_overdue_filter"
        )
        
        if pending_df.empty:
            st.info("🎉 Tuyệt vời! Không có hồ sơ nào tồn đọng chưa gửi cho Kế toán.")
        else:
            # Lọc sạch NaN của client_received_date của luồng tracking gốc cũ để tính ngày trễ
            pending_df = pending_df.dropna(subset=["client_received_date"])
            
            if pending_df.empty:
                st.info("🎉 Tuyệt vời! Không có hồ sơ hợp lệ nào tồn đọng.")
            else:
                pending_df["client_received_date_dt"] = pd.to_datetime(pending_df["client_received_date"], errors="coerce")
                today_dt = pd.Timestamp.today().normalize()
                pending_df["days_delayed"] = (today_dt - pending_df["client_received_date_dt"]).dt.days
                
                display_pending = pending_df.copy()
                if search_keyword:
                    kw = search_keyword.lower()
                    display_pending = display_pending[
                        display_pending.astype(str).apply(lambda col: col.str.lower()).apply(lambda col: col.str.contains(kw, na=False)).any(axis=1)
                    ]
                    
                if overdue_filter_pending == "🚨 Chỉ đơn quá hạn (≥ 3 ngày)":
                    display_pending = display_pending[display_pending["days_delayed"] >= 3]
                elif overdue_filter_pending == "🟢 Chỉ đơn trong hạn (< 3 ngày)":
                    display_pending = display_pending[display_pending["days_delayed"] < 3]
                
                if display_pending.empty:
                    st.warning("Không tìm thấy đơn chờ gửi nào khớp với điều kiện lọc.")
                else:
                    # Render bảng AgGrid chọn hàng loạt chuẩn chỉnh của Chỗ thứ 2
                    grid_data = display_pending[["document_tracking_id", "order_number", "customer_name", "client_received_date", "days_delayed"]].copy()
                    grid_data.columns = ["ID", "Mã Đơn Hàng", "Tên Khách Hàng", "Ngày Nhận Từ Khách", "Số Ngày Trễ"]
                    
                    gb = GridOptionsBuilder.from_dataframe(grid_data)
                    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)
                    gb.configure_default_column(resizable=True, filter=True, sortable=True)
                    gb.configure_selection(selection_mode="multiple", use_checkbox=True, header_checkbox=True)
                    gb.configure_grid_options(enableCellTextSelection=True)
                    gridOptions = gb.build()
                    
                    grid_response = AgGrid(
                        grid_data, gridOptions=gridOptions, height=350, width='100%',
                        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
                        update_mode=GridUpdateMode.SELECTION_CHANGED,
                        theme="streamlit", key=f"pending_grid_v8_{len(display_pending)}"
                    )
                    
                    with st.form("batch_accounting_transfer_form_v8"):
                        col_f1, col_f2 = st.columns(2)
                        with col_f1:
                            acc_sent_date = st.date_input("Ngày gửi cho Kế toán (Đơn hàng loạt):", value=pd.Timestamp.today().date())
                        with col_f2:
                            acc_note = st.text_input("Ghi chú nội dung bàn giao hàng loạt:", value="")
                            
                        submit_transfer = st.form_submit_button("🚀 Xác nhận gửi Kế toán các đơn đã tích chọn", use_container_width=True, type="primary")
                        
                        if submit_transfer:
                            selected_rows = grid_response.get("selected_rows", [])
                            if isinstance(selected_rows, pd.DataFrame):
                                selected_rows = selected_rows.to_dict(orient="records")
                                
                            if not selected_rows:
                                st.warning("Vui lòng tích chọn ít nhất một đơn hàng từ bảng!")
                            else:
                                selected_ids = [row["ID"] for row in selected_rows]
                                final_selected_data = pending_df[pending_df["document_tracking_id"].isin(selected_ids)].to_dict(orient="records")
                                
                                for r in final_selected_data:
                                    r["sent_to_accounting_date"] = acc_sent_date
                                    r["note"] = acc_note
                                
                                # Gọi hàm xử lý hàng loạt kèm theo log hành động
                                DocumentAccountingRepository.batch_add_accounting_flow_with_log(final_selected_data, username)
                                st.success(f"Đã bàn giao thành công {len(final_selected_data)} hồ sơ từ luồng tự động!")
                                st.rerun()

                    # --- [MỚI] NÚT DỌN DẸP ĐƠN CŨ ĐÃ XỬ LÝ (ĐẶT NGOÀI FORM ĐỂ TRÁNH LỒNG NHAU) ---
                    st.write("") # Tạo khoảng cách nhỏ
                    if st.button("🧹 Dọn đơn cũ (Đã hoàn thành trong quá khứ)", use_container_width=True):
                        selected_rows = grid_response.get("selected_rows", [])
                        if isinstance(selected_rows, pd.DataFrame):
                            selected_rows = selected_rows.to_dict(orient="records")
                        
                        if not selected_rows:
                            st.warning("Vui lòng tích chọn các đơn cũ đã xử lý xong trên bảng AgGrid ở trên!")
                        else:
                            selected_ids = [row["ID"] for row in selected_rows]
                            # Lấy dữ liệu chuẩn dựa trên ID được tích chọn
                            final_selected_data = pending_df[pending_df["document_tracking_id"].isin(selected_ids)].to_dict(orient="records")
                            
                            # Gọi hàm xử lý an toàn chúng ta vừa thêm vào Repository
                            DocumentAccountingRepository.mark_historical_done(final_selected_data, username)
                            
                            st.success(f"Đã dọn dẹp thành công {len(final_selected_data)} đơn cũ! Bảng Chỗ 2 đã được cập nhật sạch sẽ.")
                            st.rerun()
        # =========================================================================
        # 📜 TOÀN BỘ LỊCH SỬ TIẾN ĐỘ BÀN GIAO KẾ TOÁN (PHẦN TẢI FILE ĐƠN GIẢN - SAFE)
        # =========================================================================
        st.divider()
        st.subheader("📜 Lịch Sử Tiến Độ Bàn Giao Kế Toán")

        overdue_filter_history = st.selectbox(
            "Lọc theo thời gian trễ hạn (Lịch sử):",
            ["Tất cả lịch sử bàn giao", "🚨 Chỉ xem đơn từng bị trễ (Số ngày trễ khi gửi ≥ 3 ngày)", "🟢 Chỉ xem đơn đúng hạn"],
            index=0,
            key="history_overdue_filter"
        )

        if filtered_history_df.empty:
            st.info("Chưa có dữ liệu lịch sử tiến độ giao nhận kế toán.")
        else:
            display_history = filtered_history_df.copy()
            
            display_history["client_received_date_dt"] = pd.to_datetime(display_history["client_received_date"], errors="coerce")
            display_history["sent_to_accounting_date_dt"] = pd.to_datetime(display_history["sent_to_accounting_date"], errors="coerce")
            display_history["days_delayed_history"] = (display_history["sent_to_accounting_date_dt"] - display_history["client_received_date_dt"]).dt.days.fillna(0)
            
            if search_keyword:
                kw = search_keyword.lower()
                display_history = display_history[
                    display_history.astype(str).apply(lambda col: col.str.lower()).apply(lambda col: col.str.contains(kw, na=False)).any(axis=1)
                ]
                
            if overdue_filter_history == "🚨 Chỉ xem đơn từng bị trễ (Số ngày trễ khi gửi ≥ 3 ngày)":
                display_history = display_history[display_history["days_delayed_history"] >= 3]
            elif overdue_filter_history == "🟢 Chỉ xem đơn đúng hạn":
                display_history = display_history[display_history["days_delayed_history"] < 3]
                
            if display_history.empty:
                st.info("Không tìm thấy lịch sử nào khớp với điều kiện lọc.")
            else:
                # Chuẩn bị dữ liệu hiển thị gốc
                history_grid_data = display_history[[
                    "id", "order_number", "customer_name", "client_received_date", 
                    "sent_to_accounting_date", "accounting_received_date", "is_received_by_accounting", "note"
                ]].copy()
                
                history_grid_data["is_received_by_accounting"] = history_grid_data["is_received_by_accounting"].map({True: "✅ Đã nhận", False: "⏳ Chờ xác nhận"})

                
                # -----------------------------------------------------------------
                # 🎛️ BỘ ĐIỀU KHIỂN PHÂN TRANG VÀ SỐ DÒNG (DO PYTHON QUẢN LÝ 100%)
                # -----------------------------------------------------------------
                source_df = history_grid_data.copy()
                total_records = len(source_df)

                # Thiết lập các cột để dàn hàng ngang bộ điều khiển phân trang
                col_ps1, col_ps2, col_ps3 = st.columns([4, 3, 3])
                
                # 1. Ô chọn số dòng hiển thị trên một trang
                with col_ps1:
                    chosen_page_size = st.selectbox(
                        "Số dòng hiển thị trên bảng:",
                        [5, 20, 50, 100],
                        index=0,
                        key="acc_history_page_size_selector_final"
                    )
                
                # Tính toán tổng số trang dựa trên số dòng đã chọn
                import math
                max_pages_calc = math.ceil(total_records / chosen_page_size) if total_records > 0 else 1

                # Khởi tạo giá trị trang hiện tại trong session_state nếu chưa có
                page_state_key = "acc_history_current_page_state"
                if page_state_key not in st.session_state:
                    st.session_state[page_state_key] = 1

                # Phòng ngừa trường hợp đổi số dòng làm tổng số trang giảm xuống thấp hơn trang hiện tại
                if st.session_state[page_state_key] > max_pages_calc:
                    st.session_state[page_state_key] = max_pages_calc

                # 2. Ô nhập số trang và hiển thị tổng số trang (Thay thế hoàn toàn phần bị mất)
                with col_ps2:
                    current_page = st.number_input(
                        f"Đến trang (tối đa {max_pages_calc}):",
                        min_value=1,
                        max_value=max_pages_calc,
                        value=st.session_state[page_state_key],
                        step=1,
                        key="acc_history_page_number_input"
                    )
                    # Cập nhật lại session_state khi người dùng nhập số trang mới
                    st.session_state[page_state_key] = current_page

                # 3. Hiển thị thông tin tổng số dòng để người dùng dễ theo dõi
                with col_ps3:
                    st.markdown("<br>", unsafe_allow_html=True) # Tạo khoảng cách nhỏ để thẳng hàng với ô nhập
                    st.info(f"Tổng số: {total_records} dòng")

                # 4. Tính toán dải dòng thực tế cần lấy dựa trên trang đang chọn
                current_page_index = current_page - 1
                start_row = current_page_index * chosen_page_size
                end_row = min(start_row + chosen_page_size, total_records)

                # Cắt dữ liệu trực tiếp bằng Python trước khi đưa vào bảng
                sliced_display_df = source_df.iloc[start_row:end_row].copy()

                # 📊 RENDER BẢNG AGGRID (Hiển thị mượt mà, không giật lag)
                grid_response = render_aggrid(
                    sliced_display_df,      # Chỉ truyền dữ liệu của trang hiện tại vào
                    key="acc_history_master_grid_final", 
                    pagination=False,       # Tắt phân trang mặc định của AgGrid vì chúng ta đã tự làm ở trên
                    height=400            # Chiều cao gọn gàng, đẹp mắt
                )

                # -----------------------------------------------------------------
                # 📥 KHU VỰC XUẤT EXCEL TỰ ĐỘNG (ĐỒNG BỘ CHÍNH XÁC THEO TRANG)
                # -----------------------------------------------------------------
                import io

                def to_excel(df):
                    if df is None or df.empty:
                        return None
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name='Lich_Su_Ban_Giao')
                    processed_data = output.getvalue()
                    return processed_data

                # 1. Chuẩn bị dữ liệu xuất TOÀN BỘ
                full_export_df = filtered_history_df.copy()
                if "is_received_by_accounting" in full_export_df.columns:
                    full_export_df["is_received_by_accounting"] = full_export_df["is_received_by_accounting"].map({True: "Đã nhận", False: "Chờ xác nhận"})
                
                try:
                    excel_data_all = to_excel(full_export_df)
                except Exception as e:
                    excel_data_all = None
                    st.error(f"Lỗi chuẩn bị dữ liệu xuất toàn bộ: {e}")

                # 2. Trích xuất dữ liệu của trang hiện tại (Trùng khớp 100% với dữ liệu hiển thị trên bảng)
                try:
                    current_page_only_df = source_df.iloc[start_row:end_row].copy()
                    excel_data_filtered = to_excel(current_page_only_df)
                except Exception as e:
                    excel_data_filtered = None
                    st.error(f"Lỗi trích xuất dữ liệu trang: {e}")

                # 3. Đưa 2 nút Export hiển thị song song bên dưới bảng
                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    if excel_data_all:
                        st.download_button(
                            label="📥 Xuất Toàn Bộ Lịch Sử (Excel)",
                            data=excel_data_all,
                            file_name="Toan_Bo_Lich_Su_Ban_Giao.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                            key="btn_export_all_excel_final"
                        )

                with col_btn2:
                    if excel_data_filtered is not None:
                        st.download_button(
                            label=f"🔍 Xuất Trang Hiện Tại ({len(current_page_only_df)} dòng - Excel)",
                            data=excel_data_filtered,
                            file_name=f"Trang_{current_page}_Hien_Tai_{len(current_page_only_df)}_Dong.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                            key="btn_export_filtered_excel_final"
                        )

                st.write("") # Tạo khoảng cách nhỏ trước khi đến phần Hoàn tác
                # -----------------------------------------------------------------

                # 🔄 HOÀN TÁC ĐƠN HÀNG GỬI NHẦM (DÀNH CHO ĐIỀU PHỐI) - FIX BUG NaN
                st.markdown("##### 🔄 Hoàn tác đơn hàng gửi nhầm (Dành cho Điều phối)")
                
                undoable_df = display_history[
                    (display_history["is_received_by_accounting"] == False) & 
                    (display_history["sent_to_accounting_date"].notna())
                ]
                
                if not undoable_df.empty:
                    undo_options = {}
                    for _, row in undoable_df.iterrows():
                        cust_name = str(row['customer_name'])
                        if not cust_name or cust_name == "None" or cust_name == "nan":
                            cust_name = f"Gửi ngoài luồng ({str(row['note'])[:20]}...)"
                            
                        label = f"Mã đơn: {row['order_number']} | Đối tượng: {cust_name} (Gửi ngày: {row['sent_to_accounting_date']})"
                        undo_options[label] = (row["id"], row["order_number"])
                        
                    col_undo1, col_undo2 = st.columns([7, 3])
                    with col_undo1:
                        selected_undo_label = st.selectbox("Chọn đơn hàng muốn rút lại / hoàn tác:", list(undo_options.keys()), key="acc_undo_select_box_v10")
                        target_undo_id, target_order_num = undo_options[selected_undo_label]
                    with col_undo2:
                        st.write("") 
                        st.write("") 
                        if st.button("↩️ Xác nhận hoàn tác gửi", use_container_width=True, type="secondary", key="btn_undo_execution_v10"):
                            DocumentAccountingRepository.rollback_accounting_flow(target_undo_id, target_order_num, username)
                            st.success(f"Đã rút lại đơn {target_order_num} thành công!")
                            st.rerun()
                else:
                    st.caption("ℹ️ Không có đơn hàng nào đang ở trạng thái 'Chờ xác nhận' để có thể hoàn tác gửi.")
    # =========================================================================
    # ⚙️ KHU VỰC XỬ LÝ CỦA KẾ TOÁN (Chỉ ADMIN và ACCOUNTANT nhìn thấy)
    # =========================================================================
    if role in ["ADMIN", "ACCOUNTANT"]:
        st.divider()
        st.info("⚙️ KHU VỰC XỬ LÝ CỦA KẾ TOÁN")
        
        if not all_history_df.empty:
            accounting_pending = all_history_df[
                (all_history_df["is_received_by_accounting"] == False) & 
                (all_history_df["sent_to_accounting_date"].notna())
            ]
        else:
            accounting_pending = pd.DataFrame()
        
       # --- PHẦN 1: QUẢN LÝ ĐƠN HÀNG (Bọc trong Hệ thống Tab) ---
        tab_pending, tab_overdue = st.tabs([
            "📥 Đơn Chờ Duyệt Ký Nhận", 
            "🚨 Cảnh Báo Đơn Quá Hạn Bàn Giao"
        ])

        # =========================================================================
        # TAB 1: ĐƠN CHỜ DUYỆT (Giữ nguyên 100% logic xử lý AgGrid và Form của bạn)
        # =========================================================================
        with tab_pending:
            if accounting_pending.empty:
                st.info("🎉 Hiện tại không có đơn hàng nào đang ở trạng thái chờ Kế toán duyệt ký nhận.")
            else:
                acc_search_keyword = st.text_input(
                    "🔍 Tìm nhanh đơn chờ duyệt (Gõ tên khách, mã đơn...):", 
                    value="", 
                    key="accounting_panel_search_filter"
                )
                
                display_acc_pending = accounting_pending.copy()
                if acc_search_keyword:
                    kw_acc = acc_search_keyword.lower()
                    display_acc_pending = display_acc_pending[
                        display_acc_pending.astype(str).apply(lambda col: col.str.lower()).apply(lambda col: col.str.contains(kw_acc, na=False)).any(axis=1)
                    ]
                
                st.markdown(f"📊 **Bảng Theo Dõi Đơn Hàng Chờ Kế Toán Duyệt ({len(display_acc_pending)} đơn):**")
                
                acc_view_df = display_acc_pending[[
                    "id", "order_number", "customer_name", "sent_to_accounting_date", "note"
                ]].copy()
                
                acc_view_df["sent_to_accounting_date"] = acc_view_df["sent_to_accounting_date"].astype(str)
                acc_view_df.columns = ["ID Luồng", "Mã Đơn Hàng", "Tên Khách Hàng", "Ngày Gửi", "Ghi Chú Đính Kèm"]
                
                gb_acc = GridOptionsBuilder.from_dataframe(acc_view_df)
                gb_acc.configure_pagination(paginationAutoPageSize=False, paginationPageSize=10)
                gb_acc.configure_default_column(resizable=True, sortable=True, filter=True)
                
                gb_acc.configure_selection(
                    selection_mode="multiple", 
                    use_checkbox=True, 
                    header_checkbox=True,
                    header_checkbox_filtered_only=True
                )
                
                grid_options_extra = {
                    "enableCellTextSelection": True,
                    "ensureDomOrder": True,
                    "suppressRowClickSelection": True
                }
                gb_acc.configure_grid_options(**grid_options_extra)
                
                gridOptions_acc = gb_acc.build()
                dynamic_acc_grid_key = f"accounting_action_grid_v9_{len(acc_view_df)}"
                
                grid_response_acc = AgGrid(
                    acc_view_df,
                    gridOptions=gridOptions_acc,
                    height=300,
                    width='100%',
                    data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
                    update_mode=GridUpdateMode.SELECTION_CHANGED,
                    fit_columns_on_grid_load=True,
                    theme="streamlit",
                    key=dynamic_acc_grid_key
                )
                
                selected_acc_rows = grid_response_acc.get("selected_rows", [])
                if isinstance(selected_acc_rows, pd.DataFrame):
                    selected_acc_rows = selected_acc_rows.to_dict(orient="records")
                    
                if selected_acc_rows:
                    selected_count = len(selected_acc_rows)
                    st.markdown(f"🔥 **Đang chọn xử lý đồng loạt:** `{selected_count}` đơn hàng.")
                    
                    with st.form("accounting_batch_action_form_v9"):
                        col_acc_date, col_acc_reason = st.columns([3, 7])
                        with col_acc_date:
                            acc_actual_recv_date = st.date_input("Ngày thực tế ký nhận:", value=pd.Timestamp.today().date(), key="acc_form_date_v9")
                        with col_acc_reason:
                            reject_reason = st.text_input("Lý do từ chối (Chỉ điền nếu bấm Từ Chối):", value="", placeholder="Ví dụ: Thiếu hóa đơn đỏ, sai số tiền...", key="acc_form_reason_v9")
                        
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            submit_approve = st.form_submit_button("📥 Xác nhận: ĐÃ nhận đủ hồ sơ (Các đơn đã chọn)", use_container_width=True, type="primary")
                            if submit_approve:
                                for row in selected_acc_rows:
                                    DocumentAccountingRepository.accountant_confirm_receive(row["ID Luồng"], row["Mã Đơn Hàng"], acc_actual_recv_date, username)
                                st.success(f"Đã ký nhận thành công cho toàn bộ {selected_count} đơn hàng được chọn!")
                                st.rerun()
                                
                        with col_btn2:
                            submit_reject = st.form_submit_button("❌ Từ chối nhận các hồ sơ đang tích chọn", use_container_width=True, type="secondary")
                            if submit_reject:
                                if not reject_reason.strip():
                                    st.error("Bạn phải nhập lý do từ chối vào ô trống phía trên trước khi bấm từ chối hàng loạt!")
                                else:
                                    for row in selected_acc_rows:
                                        DocumentAccountingRepository.reject_accounting_flow(row["ID Luồng"], reject_reason.strip(), order_number=row["Mã Đơn Hàng"], username=username)
                                    st.warning(f"Đã từ chối bàn giao {selected_count} đơn hàng và chuyển trả lại danh sách chờ gửi.")
                                    st.rerun()
                else:
                    st.caption("💡 *Mẹo cho Kế toán: Tích chọn vào ô vuông ở đầu một hoặc nhiều dòng trong bảng để xử lý duyệt/từ chối hàng loạt.*")

        # =========================================================================
        # TAB 2: ĐƠN QUÁ HẠN (Đã sửa Phân trang thủ công, Đổi sang Assistant, Xuất Excel)
        # =========================================================================
        with tab_overdue:
            st.warning("🚨 Danh sách đơn hàng đã tạo lâu nhưng Trợ lý (Assistant) chưa bàn giao chứng từ cho Kế toán.")
            
            # --- KHU VỰC BỘ LỌC CẤU HÌNH ---
            col_days, col_start_date = st.columns(2)
            with col_days:
                days_limit = st.number_input(
                    "⏰ Số ngày trễ tối thiểu:", 
                    min_value=1, max_value=90, value=7, step=1, 
                    key="acc_overdue_days_input"
                )
            with col_start_date:
                # Vấn đề 1: Cho phép kế toán cấu hình ngày bắt đầu áp dụng để loại bỏ đơn cũ lịch sử
                system_start_date = st.date_input(
                    "📅 Chỉ quét đơn từ ngày:", 
                    value=pd.Timestamp("2026-06-01").date(),
                    key="acc_overdue_start_date_input"
                )

            # Gọi hàm repository cập nhật
            overdue_df = DocumentAccountingRepository.get_overdue_documents(
                days_limit=days_limit, 
                start_date=str(system_start_date)
            )
            
            if overdue_df.empty:
                st.success(f"🎉 Tuyệt vời! Không có đơn hàng nào trễ quá {days_limit} ngày tính từ {system_start_date}.")
            else:
                st.error(f"⚠️ Phát hiện **{len(overdue_df)}** đơn hàng quá hạn chưa nhận được chứng từ!")
                
                # --- VẤN ĐỀ 4: NÚT XUẤT EXCEL TỔNG HỢP ---
                import io
                overdue_excel_buffer = io.BytesIO()
                with pd.ExcelWriter(overdue_excel_buffer, engine='xlsxwriter') as writer:
                    overdue_df.to_excel(writer, sheet_name='Don_Qua_Han', index=False)
                
                st.download_button(
                    label="📥 Xuất Danh Sách Quá Hạn (Excel)",
                    data=overdue_excel_buffer.getvalue(),
                    file_name=f"don_qua_han_chua_ban_giao_{pd.Timestamp.today().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="btn_export_overdue_excel"
                )
                
                # Chuẩn bị dữ liệu hiển thị
                display_overdue = overdue_df.copy()
                if "Ngày Nhận Từ Khách" in display_overdue.columns:
                    try:
                        display_overdue["Ngày Nhận Từ Khách"] = pd.to_datetime(display_overdue["Ngày Nhận Từ Khách"]).dt.strftime('%Y-%m-%d %H:%M')
                    except Exception:
                        pass

                # --- VẤN ĐỀ 2: TỰ TẠO PHÂN TRANG ĐIỀU KHIỂN BẢNG AGGRID ---
                st.write("---")
                col_page_size, col_page_num = st.columns([4, 6])
                
                with col_page_size:
                    page_size = st.selectbox(
                        "📄 Số lượng dòng hiển thị:", 
                        options=[5, 10, 20, 50, 100], 
                        index=1, 
                        key="overdue_page_size_select"
                    )
                
                # Tính toán tổng số trang dựa trên size được chọn
                total_rows = len(display_overdue)
                total_pages = max(1, int(np.ceil(total_rows / page_size)))
                
                with col_page_num:
                    current_page = st.number_input(
                        f"🔢 Nhảy đến trang (1 - {total_pages}):", 
                        min_value=1, 
                        max_value=total_pages, 
                        value=1, 
                        step=1, 
                        key="overdue_current_page_input"
                    )
                
                # Cắt lát dữ liệu DataFrame theo phân trang Python quyết định
                start_idx = (current_page - 1) * page_size
                end_idx = start_idx + page_size
                sliced_display_df = display_overdue.iloc[start_idx:end_idx]
                
                # Dựng cấu hình AgGrid thủ công (Tắt chế độ phân trang mặc định của AgGrid)
                gb_ov = GridOptionsBuilder.from_dataframe(sliced_display_df)
                gb_ov.configure_default_column(resizable=True, sortable=True, filter=True)
                
                grid_options_ov_extra = {
                    "enableCellTextSelection": True,
                    "ensureDomOrder": True,
                    "suppressPaginationPanel": True # Tắt hoàn toàn thanh điều khiển phân trang mặc định ở đáy của AgGrid
                }
                gb_ov.configure_grid_options(**grid_options_ov_extra)
                gridOptions_ov = gb_ov.build()
                
                # Hiển thị bảng
                AgGrid(
                    sliced_display_df,
                    gridOptions=gridOptions_ov,
                    height=280,
                    width='100%',
                    fit_columns_on_grid_load=True,
                    theme="streamlit",
                    key=f"accounting_overdue_controlled_grid_page_{current_page}_size_{page_size}"
                )
                
                st.caption(f"📊 *Hiển thị dòng {start_idx + 1} đến {min(end_idx, total_rows)} trên tổng số {total_rows} dòng.*")
                st.caption("💡 *Mẹo: Kế toán dựa vào cột 'Trợ Lý Phụ Trách' để đôn đốc nhân viên hoàn thiện hồ sơ.*")
        # =========================================================================
        # ↩️ KHU VỰC CỨU HỘ: HOÀN TÁC KHẨN CẤP CHO KẾ TOÁN (LUÔN HIỂN THỊ)
        # =========================================================================
        # (Đoạn này đã được đưa ra ngoài dấu thụt lề của nhánh `else` phía trên)
        st.write("---")
        with st.expander("↩️ Khu vực Hoàn Tác nhanh (Dành cho đơn lỡ tay bấm Xác Nhận)"):
            recent_df = DocumentAccountingRepository.get_recently_received_flows(limit=5)
            
            if recent_df.empty:
                st.info("Chưa có đơn hàng nào được xác nhận gần đây để hoàn tác.")
            else:
                st.caption("Dưới đây là 5 đơn hàng vừa được ký nhận gần nhất. Bạn có thể bấm hoàn tác để trả lại Chỗ 2:")
                
                for idx, row in recent_df.iterrows():
                    col_info, col_btn = st.columns([4, 1])
                    with col_info:
                        st.markdown(
                            f"📦 **Đơn: {row['order_number']}** | Sale: {row['sale_owner']} | "
                            f"Ngày nhận: {row['accounting_received_date']} | *Ghi chú cũ: {row['note'] or ''}*"
                        )
                    with col_btn:
                        undo_clicked = st.button(
                            "↩️ Hoàn tác", 
                            key=f"quick_undo_{row['id']}", 
                            type="secondary",
                            use_container_width=True
                        )
                        if undo_clicked:
                            DocumentAccountingRepository.accountant_undo_receive(
                                flow_id=row['id'], 
                                order_number=row['order_number'], 
                                username=st.session_state["username"]
                            )
                            st.success(f"Đã hoàn tác thành công đơn {row['order_number']} về Chỗ 2!")
                            st.rerun()

        # =========================================================================
        # 📜 PHẦN 3: HIỂN THỊ BẢNG NHẬT KÝ HÀNH ĐỘNG CHI TIẾT (AUDIT LOGS)
        # =========================================================================
        st.markdown("### 📋 Nhật Ký Hành Động Kế Toán (Audit Trail)")
        logs_df = DocumentAccountingRepository.get_action_logs()
        if logs_df.empty:
            st.caption("Chưa có bất kỳ hành động thao tác hệ thống nào của kế toán được ghi nhận.")
        else:
            display_logs = logs_df.copy()
            action_map = {
                "SEND": "📤 Gửi từ Tracking",
                "SEND_DIRECT": "⚡ Gửi Trực Tiếp",
                "APPROVE": "📥 Ký Nhận",
                "REJECT": "❌ Từ Chối",
                "UNDO": "↩️ Hoàn Tác",
                "ACCOUNTANT_UNDO": "🔄 Kế toán hoàn tác"
            }
            display_logs["action_type"] = display_logs["action_type"].map(action_map).fillna(display_logs["action_type"])
            display_logs.columns = ["Mã Đơn Hàng", "Loại Hành Động", "Người Thực Hiện", "Chi Tiết Nhật Ký", "Thời Gian Hệ Thống"]
            
            render_aggrid(display_logs, key="accounting_audit_trail_logs_grid")
            
        st.write("### 📜 Lịch sử thao tác (Logs)")

        if not logs_df.empty:
            df_excel = logs_df.copy()
            for col in df_excel.columns:
                if pd.api.types.is_datetime64_any_dtype(df_excel[col]) or df_excel[col].dtype == 'object':
                    try:
                        df_excel[col] = pd.to_datetime(df_excel[col], errors='ignore').dt.strftime('%Y-%m-%d %H:%M:%S')
                    except Exception:
                        pass

            import io
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_excel.to_excel(writer, sheet_name='Logs_KeToan', index=False)
            
            col_l1, col_l2 = st.columns([1, 1])
            
            with col_l1:
                st.download_button(
                    label="📥 Xuất Lịch Sử Log (Excel)",
                    data=buffer.getvalue(),
                    file_name=f"log_ke_toan_{pd.Timestamp.today().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                
            with col_l2:
                with st.popover("🚨 Xóa Lịch Sử Log", use_container_width=True):
                    st.warning("Hành động này sẽ xóa toàn bộ log hiện tại! Bạn đã xuất Excel để lưu trữ chưa?")
                    confirm_clear = st.button("Tôi chắc chắn, tiến hành xóa sạch log", type="primary", use_container_width=True)
                    if confirm_clear:
                        DocumentAccountingRepository.clear_all_action_logs(st.session_state["username"])
                        st.success("Đã xóa sạch lịch sử log!")
                        st.rerun()
        else:
            st.info("Hiện tại chưa có log lịch sử nào.")