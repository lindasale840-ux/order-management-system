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
                    st.error(f"🚨 **CẢNH BÁO: Phát hiện {actual_overdue_count} đơn hàng chờ gửi đã quá hạn trên 3 ngày!**")
                
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
                
                grid_response = AgGrid(
                    grid_data,
                    gridOptions=gridOptions,
                    height=400,
                    width='100%',
                    data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
                    update_mode=GridUpdateMode.SELECTION_CHANGED,
                    fit_columns_on_grid_load=True,
                    theme="streamlit",
                    key="custom_pending_accounting_grid"
                )
                
                with st.form("batch_accounting_transfer_form_v6"):
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
    
    # Thêm bộ lọc trạng thái/trễ hạn riêng cho bảng Lịch sử theo ý bạn
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
        
        # Áp dụng tính toán ngày trễ phục vụ cho bộ lọc lịch sử
        display_history["client_received_date_dt"] = pd.to_datetime(display_history["client_received_date"], errors="coerce")
        display_history["sent_to_accounting_date_dt"] = pd.to_datetime(display_history["sent_to_accounting_date"], errors="coerce")
        display_history["days_delayed_history"] = (display_history["sent_to_accounting_date_dt"] - display_history["client_received_date_dt"]).dt.days
        
        # Áp dụng bộ lọc từ khóa tổng
        if search_keyword:
            kw = search_keyword.lower()
            display_history = display_history[
                display_history.astype(str).apply(lambda col: col.str.lower()).apply(lambda col: col.str.contains(kw, na=False)).any(axis=1)
            ]
            
        # Áp dụng bộ lọc trễ hạn lịch sử vừa thêm
        if overdue_filter_history == "🚨 Chỉ xem đơn từng bị trễ (Số ngày trễ khi gửi ≥ 3 ngày)":
            display_history = display_history[display_history["days_delayed_history"] >= 3]
        elif overdue_filter_history == "🟢 Chỉ xem đơn đúng hạn":
            display_history = display_history[display_history["days_delayed_history"] < 3]
            
        if display_history.empty:
            st.info("Không tìm thấy lịch sử nào khớp với điều kiện lọc.")
        else:
            # Chuẩn bị dữ liệu đưa vào bảng gốc
            history_grid_data = display_history[[
                "id", "order_number", "customer_name", "client_received_date", 
                "sent_to_accounting_date", "accounting_received_date", "is_received_by_accounting", "note"
            ]].copy()
            
            history_grid_data["is_received_by_accounting"] = history_grid_data["is_received_by_accounting"].map({True: "✅ Đã nhận", False: "⏳ Chờ xác nhận"})
            
            # ĐÃ XÓA KHỐI LỆNH LỰA CHỌN PHÂN TRANG THỦ CÔNG THỪA Ở ĐÂY
            # Truyền thẳng dữ liệu vào hàm gốc để AgGrid tự quản lý hiển thị, bộ lọc nội bộ và phân trang đồng bộ
            render_aggrid(history_grid_data, key="acc_history_master_grid_v6")

    # =========================================================================
    # ⚙️ KHU VỰC XỬ LÝ CỦA KẾ TOÁN (Chỉ ADMIN và ACCOUNTANT nhìn thấy)
    # =========================================================================
    if role in ["ADMIN", "ACCOUNTANT"]:
        st.divider()
        st.info("⚙️ KHU VỰC XỬ LÝ CỦA KẾ TOÁN")
        
        accounting_pending_confirm = all_history_df[all_history_df["is_received_by_accounting"] == False] if not all_history_df.empty else pd.DataFrame()
        
        if accounting_pending_confirm.empty or "is_received_by_accounting" not in accounting_pending_confirm.columns:
            st.info("Hiện không có đơn hàng nào đang ở trạng thái chờ Kế toán duyệt ký nhận.")
        else:
            st.markdown(f"Có **{len(accounting_pending_confirm)}** đơn hàng đang chờ bạn kiểm tra và ký nhận.")
            
            acc_confirm_options = {
                f"Đơn: {row['order_number']} | Khách: {row['customer_name']} | Ngày gửi: {row['sent_to_accounting_date']}": (row["id"], row["order_number"])
                for _, row in accounting_pending_confirm.iterrows()
            }
            
            col_acc1, col_acc2 = st.columns([7, 3])
            with col_acc1:
                selected_flow_label = st.selectbox("Chọn đơn hàng bàn giao thực tế:", list(acc_confirm_options.keys()), key="acc_real_select_box_v6")
                target_flow_id, target_order_num = acc_confirm_options[selected_flow_label]
            with col_acc2:
                acc_actual_recv_date = st.date_input("Ngày bạn ký nhận", value=pd.Timestamp.today().date(), key="acc_real_date_input_v6")
                
            if st.button("📥 Xác nhận: ĐÃ nhận đủ hồ sơ giấy tờ", use_container_width=True, type="secondary"):
                DocumentAccountingService.confirm_receipt_by_accountant(target_flow_id, target_order_num, acc_actual_recv_date)
                st.success(f"Xác nhận thành công! Đơn {target_order_num} đã được ghi nhận ĐÃ KÝ NHẬN tại phòng Kế toán.")
                st.rerun()