import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
from repositories.document_accounting_repository import DocumentAccountingRepository
from services.document_accounting_service import DocumentAccountingService
from components.aggrid_table import render_aggrid # Giữ nguyên hàm gốc để đảm bảo định dạng và không lỗi trang khác
from utils.data_permission import filter_by_sale_owner
from utils.auth_guard import require_editor

def show_document_accounting_page():
    require_editor()
    
    st.title("📑 Điều Phối & Bàn Giao Hồ Sơ Kế Toán")
    role = st.session_state.get("role")
    username = st.session_state.get("username")
    
    # 1. Lấy dữ liệu từ nguồn và xử lý phân quyền
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

    # =========================================================================
    # 🔍 BỘ LỌC TỔNG THÔNG MINH (Dùng chung từ khóa tìm kiếm)
    # =========================================================================
    st.markdown("### 🔍 Bộ Lọc Tìm Kiếm Nhanh")
    search_keyword = st.text_input("Gõ từ khóa để lọc nhanh trên cả 2 bảng (Mã đơn, Tên khách hàng...):", value="", key="main_search_filter")

    # =========================================================================
    # 📥 DANH SÁCH ĐƠN CHỜ GỬI KẾ TOÁN (BẢNG CÓ CHECKBOX CHỌN HÀNG LOẠT)
    # =========================================================================
    st.divider()
    st.subheader("📥 Danh Sách Đơn Chờ Gửi Kế Toán")
    
    # Bộ lọc trễ hạn riêng cho bảng Chờ gửi
    overdue_filter_pending = st.selectbox(
        "Lọc theo thời gian trễ hạn (Chờ gửi):",
        ["Tất cả đơn chờ gửi", "🚨 Chỉ đơn quá hạn (≥ 3 ngày)", "🟢 Chỉ đơn trong hạn (< 3 ngày)"],
        index=0,
        key="pending_overdue_filter"
    )
    
    if pending_df.empty:
        st.info("🎉 Tuyệt vời! Không có hồ sơ nào tồn đọng chưa gửi cho Kế toán.")
    else:
        pending_df = pending_df.dropna(subset=["client_received_date"])
        
        if pending_df.empty:
            st.info("🎉 Tuyệt vời! Không có hồ sơ hợp lệ nào tồn đọng.")
        else:
            # Tính toán số ngày trễ hạn động
            pending_df["client_received_date_dt"] = pd.to_datetime(pending_df["client_received_date"], errors="coerce")
            today_dt = pd.Timestamp.today().normalize()
            pending_df["days_delayed"] = (today_dt - pending_df["client_received_date_dt"]).dt.days
            
            # Áp dụng bộ lọc lên dữ liệu Chờ gửi
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
                actual_overdue_count = len(display_pending[display_pending["days_delayed"] >= 3])
                if actual_overdue_count > 0:
                    st.error(f"🚨 **CẢNH BÁO: Phân tích phát hiện {actual_overdue_count} đơn hàng chờ gửi đã quá hạn trên 3 ngày!**")
                
                grid_data = display_pending[[
                    "document_tracking_id", "order_number", "customer_name", "client_received_date", "days_delayed"
                ]].copy()
                grid_data.columns = ["ID", "Mã Đơn Hàng", "Tên Khách Hàng", "Ngày Nhận Từ Khách", "Số Ngày Trễ"]
                
                gb = GridOptionsBuilder.from_dataframe(grid_data)
                gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)
                gb.configure_default_column(resizable=True, filter=True, sortable=True)
                gb.configure_selection(
                    selection_mode="multiple", 
                    use_checkbox=True, 
                    header_checkbox=True,
                    header_checkbox_filtered_only=True
                )
                gridOptions = gb.build()
                
                # SỬA BUG: Thêm len(display_pending) vào key để buộc làm mới hoàn toàn trạng thái Checkbox khi số lượng dòng thay đổi
                dynamic_grid_key = f"custom_pending_accounting_grid_len_{len(display_pending)}"
                
                grid_response = AgGrid(
                    grid_data,
                    gridOptions=gridOptions,
                    height=400,
                    width='100%',
                    data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
                    update_mode=GridUpdateMode.SELECTION_CHANGED,
                    fit_columns_on_grid_load=True,
                    theme="streamlit",
                    key=dynamic_grid_key
                )
                
                with st.form("batch_accounting_transfer_form_v7"):
                    col_f1, col_f2 = st.columns(2)
                    with col_f1:
                        acc_sent_date = st.date_input("Ngày thực tế gửi cho Kế toán", value=pd.Timestamp.today().date())
                    with col_f2:
                        acc_note = st.text_input("Ghi chú nội dung bàn giao", value="", placeholder="Ví dụ: Gửi kèm hóa đơn đỏ...")
                        
                    submit_transfer = st.form_submit_button("🚀 Xác nhận gửi Kế toán các đơn đã chọn", use_container_width=True, type="primary")
                    
                    if submit_transfer:
                        selected_rows = grid_response.get("selected_rows", [])
                        if isinstance(selected_rows, pd.DataFrame):
                            selected_rows = selected_rows.to_dict(orient="records")
                            
                        if not selected_rows:
                            st.warning("Vui lòng tích chọn ít nhất một đơn hàng từ bảng dữ liệu phía trên trước khi xác nhận gửi!")
                        else:
                            selected_ids = [row["ID"] for row in selected_rows]
                            final_selected_data = pending_df[pending_df["document_tracking_id"].isin(selected_ids)].to_dict(orient="records")
                            
                            DocumentAccountingService.send_documents_to_accounting(final_selected_data, acc_sent_date, acc_note)
                            st.success(f"Đã bàn giao thành công {len(final_selected_data)} hồ sơ!")
                            st.rerun()

    # =========================================================================
    # 📜 TOÀN BỘ LỊCH SỬ TIẾN ĐỘ BÀN GIAO KẾ TOÁN (TINH CHỈNH GỌN GÀNG)
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
        display_history["days_delayed_history"] = (display_history["sent_to_accounting_date_dt"] - display_history["client_received_date_dt"]).dt.days
        
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
            history_grid_data = display_history[[
                "id", "order_number", "customer_name", "client_received_date", 
                "sent_to_accounting_date", "accounting_received_date", "is_received_by_accounting", "note"
            ]].copy()
            
            history_grid_data["is_received_by_accounting"] = history_grid_data["is_received_by_accounting"].map({True: "✅ Đã nhận", False: "⏳ Chờ xác nhận"})
            
            render_aggrid(history_grid_data, key="acc_history_master_grid_v7")

            # -----------------------------------------------------------------
            # 🔄 YÊU CẦU 1: KHU VỰC HOÀN TÁC ĐƠN HÀNG (Dành cho Điều phối gửi nhầm)
            # -----------------------------------------------------------------
            st.markdown("##### 🔄 Hoàn tác đơn hàng gửi nhầm")
            # Chỉ cho phép hoàn tác những đơn đang ở trạng thái "Chờ xác nhận"
            undoable_df = display_history[display_history["is_received_by_accounting"] == False]
            
            if not undoable_df.empty:
                undo_options = {
                    f"Mã đơn: {row['order_number']} | Khách hàng: {row['customer_name']} (Gửi ngày: {row['sent_to_accounting_date']})": row["id"]
                    for _, row in undoable_df.iterrows()
                }
                col_undo1, col_undo2 = st.columns([7, 3])
                with col_undo1:
                    selected_undo_label = st.selectbox("Chọn đơn hàng muốn rút lại / hoàn tác:", list(undo_options.keys()), key="acc_undo_select_box")
                    target_undo_id = undo_options[selected_undo_label]
                with col_undo2:
                    st.write("") # Tạo khoảng trống căn lề
                    st.write("") 
                    if st.button("↩️ Xác nhận hoàn tác", use_container_width=True, type="secondary", key="btn_undo_execution"):
                        DocumentAccountingService.rollback_accounting_transfer(target_undo_id)
                        st.success("Đã hoàn tác trạng thái thành công! Đơn hàng đã được chuyển lại về danh sách chờ gửi.")
                        st.rerun()
            else:
                st.caption("ℹ️ Không có đơn hàng nào trong danh sách hiện tại thuộc trạng thái 'Chờ xác nhận' để có thể hoàn tác.")

    # =========================================================================
    # ⚙️ KHU VỰC XỬ LÝ CỦA KẾ TOÁN (Chỉ ADMIN và ACCOUNTANT nhìn thấy)
    # =========================================================================
    if role in ["ADMIN", "ACCOUNTANT"]:
        st.divider()
        st.info("⚙️ KHU VỰC XỬ LÝ CỦA KẾ TOÁN")
        
        # Chỉ lấy các đơn đã gửi (sent_to_accounting_date không NULL) nhưng Kế toán chưa nhận
        if not all_history_df.empty:
            accounting_pending = all_history_df[
                (all_history_df["is_received_by_accounting"] == False) & 
                (all_history_df["sent_to_accounting_date"].notna())
            ]
        else:
            accounting_pending = pd.DataFrame()
        
        if accounting_pending.empty:
            st.info("🎉 Hiện tại không có đơn hàng nào đang ở trạng thái chờ Kế toán duyệt ký nhận.")
        else:
            # -----------------------------------------------------------------
            # YÊU CẦU 2: BỘ LỌC TÌM KIẾM NHANH DÀNH RIÊNG CHO KẾ TOÁN
            # -----------------------------------------------------------------
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
            
            # Chuẩn bị dữ liệu hiển thị bảng gọn gàng cho Kế toán dễ nhìn
            acc_view_df = display_acc_pending[[
                "id", "order_number", "customer_name", "sent_to_accounting_date", "note"
            ]].copy()
            
            # Khắc phục lỗi [object Object] bằng cách ép kiểu chuỗi văn bản thuần túy
            acc_view_df["sent_to_accounting_date"] = acc_view_df["sent_to_accounting_date"].astype(str)
            acc_view_df.columns = ["ID Luồng", "Mã Đơn Hàng", "Tên Khách Hàng", "Ngày Gửi", "Ghi Chú Đính Kèm"]
            
            # Cấu hình AgGrid nâng cao cho Kế toán
            gb_acc = GridOptionsBuilder.from_dataframe(acc_view_df)
            gb_acc.configure_pagination(paginationAutoPageSize=False, paginationPageSize=10)
            
            # GIẢI ĐÁP: Thêm `filter=True` để kích hoạt ô tìm kiếm riêng ở TỪNG TIÊU ĐỀ CỘT
            gb_acc.configure_default_column(resizable=True, sortable=True, filter=True)
            
            # YÊU CẦU 1: Chuyển cấu hình từ chọn đơn lẻ ('single') sang CHỌN HÀNG LOẠT ('multiple') bằng Checkbox
            gb_acc.configure_selection(
                selection_mode="multiple", 
                use_checkbox=True, 
                header_checkbox=True,
                header_checkbox_filtered_only=True
            )
            gridOptions_acc = gb_acc.build()
            
            # Thêm độ dài danh sách vào key để tự động xóa sạch dấu tích khi số dòng thay đổi (Fix bug dính checkbox)
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
            
            # Lấy toàn bộ danh sách các dòng được tích chọn
            selected_acc_rows = grid_response_acc.get("selected_rows", [])
            if isinstance(selected_acc_rows, pd.DataFrame):
                selected_acc_rows = selected_acc_rows.to_dict(orient="records")
                
            if selected_acc_rows:
                # Đếm số lượng đơn đang được chọn để xử lý đồng loạt
                selected_count = len(selected_acc_rows)
                st.markdown(f"🔥 **Đang chọn xử lý đồng loạt:** `{selected_count}` đơn hàng.")
                
                # Bọc khu vực nhập liệu vào Form để tối ưu hóa nút bấm đồng loạt, tránh việc bấm nút này nhảy nút kia
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
                                DocumentAccountingService.confirm_receipt_by_accountant(row["ID Luồng"], row["Mã Đơn Hàng"], acc_actual_recv_date)
                            st.success(f"Đã ký nhận thành công cho toàn bộ {selected_count} đơn hàng được chọn!")
                            st.rerun()
                            
                    with col_btn2:
                        submit_reject = st.form_submit_button("❌ Từ chối nhận các hồ sơ đang tích chọn", use_container_width=True, type="secondary")
                        if submit_reject:
                            if not reject_reason.strip():
                                st.error("Bạn phải nhập lý do từ chối vào ô trống phía trên trước khi bấm từ chối hàng loạt!")
                            else:
                                for row in selected_acc_rows:
                                    DocumentAccountingService.reject_accounting_transfer(row["ID Luồng"], reject_reason.strip(), order_number=row["Mã Đơn Hàng"])
                                st.warning(f"Đã từ chối bàn giao {selected_count} đơn hàng và chuyển trả lại danh sách chờ gửi.")
                                st.rerun()
            else:
                st.caption("💡 *Mẹo cho Kế toán: Tích chọn vào ô vuông ở đầu một hoặc nhiều dòng trong bảng để xử lý duyệt/từ chối hàng loạt.*")