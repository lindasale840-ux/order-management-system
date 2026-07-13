import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
from repositories.document_accounting_repository import DocumentAccountingRepository
from services.document_accounting_service import DocumentAccountingService # Giả định service truyền username vào repo
from components.aggrid_table import render_aggrid 
from utils.data_permission import filter_by_sale_owner
from utils.auth_guard import require_editor

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
            history_grid_data = display_history[[
                "id", "order_number", "customer_name", "client_received_date", 
                "sent_to_accounting_date", "accounting_received_date", "is_received_by_accounting", "note"
            ]].copy()
            
            history_grid_data["is_received_by_accounting"] = history_grid_data["is_received_by_accounting"].map({True: "✅ Đã nhận", False: "⏳ Chờ xác nhận"})
            render_aggrid(history_grid_data, key="acc_history_master_grid_v7")

            # -----------------------------------------------------------------
            # 🔄 HOÀN TÁC ĐƠN HÀNG GỬI NHẦM (DÀNH CHO ĐIỀU PHỐI) - FIX BUG NaN
            # -----------------------------------------------------------------
            st.markdown("##### 🔄 Hoàn tác đơn hàng gửi nhầm (Dành cho Điều phối)")
            
            undoable_df = display_history[
                (display_history["is_received_by_accounting"] == False) & 
                (display_history["sent_to_accounting_date"].notna())
            ]
            
            if not undoable_df.empty:
                undo_options = {}
                for _, row in undoable_df.iterrows():
                    # Xử lý nếu tên khách hàng bị rỗng hoặc NaN (Đơn ngoài luồng) thì lấy Ghi chú đắp vào
                    cust_name = str(row['customer_name'])
                    if not cust_name or cust_name == "None" or cust_name == "nan":
                        cust_name = f"Gửi ngoài luồng ({str(row['note'])[:20]}...)"
                        
                    label = f"Mã đơn: {row['order_number']} | Đối tượng: {cust_name} (Gửi ngày: {row['sent_to_accounting_date']})"
                    undo_options[label] = (row["id"], row["order_number"])
                    
                col_undo1, col_undo2 = st.columns([7, 3])
                with col_undo1:
                    selected_undo_label = st.selectbox("Chọn đơn hàng muốn rút lại / hoàn tác:", list(undo_options.keys()), key="acc_undo_select_box_v3")
                    target_undo_id, target_order_num = undo_options[selected_undo_label]
                with col_undo2:
                    st.write("") 
                    st.write("") 
                    if st.button("↩️ Xác nhận hoàn tác gửi", use_container_width=True, type="secondary", key="btn_undo_execution_v3"):
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
                                # Truyền thêm tham số order_number và username phục vụ logs
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

            # -----------------------------------------------------------------
            # ↩️ HOÀN TÁC XỬ LÝ NHẦM (DÀNH CHO KẾ TOÁN) - THÊM MỚI
            # -----------------------------------------------------------------
            st.markdown("##### ↩️ Hoàn tác xử lý nhầm (Dành cho Kế toán)")
            
            # Kế toán có thể hoàn tác những đơn ĐÃ ký nhận (True) HOẶC những đơn có chữ 'Từ chối' trong note
            acc_undoable_df = all_history_df[
                (all_history_df["is_received_by_accounting"] == True) | 
                (all_history_df["note"].str.contains("Từ chối", na=False))
            ]
            
            if not acc_undoable_df.empty:
                acc_undo_options = {
                    f"Mã đơn: {row['order_number']} | Trạng thái hiện tại: {'Đã nhận' if row['is_received_by_accounting'] else 'Đã từ chối'}": (row["id"], row["order_number"])
                    for _, row in acc_undoable_df.iterrows()
                }
                col_a_undo1, col_a_undo2 = st.columns([7, 3])
                with col_a_undo1:
                    selected_acc_undo_label = st.selectbox("Chọn đơn hàng Kế toán muốn HOÀN TÁC lại trạng thái:", list(acc_undo_options.keys()), key="accountant_undo_select_box")
                    target_acc_flow_id, target_acc_order_num = acc_undo_options[selected_acc_undo_label]
                with col_a_undo2:
                    st.write("") 
                    st.write("") 
                    if st.button("↩️ Khôi phục về 'Chờ Duyệt'", use_container_width=True, type="secondary", key="btn_accountant_undo_execute"):
                        DocumentAccountingRepository.accountant_undo_receive(target_acc_flow_id, target_acc_order_num, username)
                        st.success(f"Đã khôi phục đơn {target_acc_order_num} về trạng thái Chờ xác nhận thành công!")
                        st.rerun()
            else:
                st.caption("ℹ️ Hiện tại chưa có đơn hàng nào được Duyệt hoặc Từ chối để có thể hoàn tác.")
        # -----------------------------------------------------------------
        # 📜 YÊU CẦU 2: HIỂN THỊ BẢNG NHẬT KÝ HÀNH ĐỘNG CHI TIẾT (AUDIT LOGS)
        # -----------------------------------------------------------------
        st.markdown("### 📋 Nhật Ký Hành Động Kế Toán (Audit Trail)")
        logs_df = DocumentAccountingRepository.get_action_logs()
        if logs_df.empty:
            st.caption("Chưa có bất kỳ hành động thao tác hệ thống nào của kế toán được ghi nhận.")
        else:
            display_logs = logs_df.copy()
            # Ánh xạ nhãn hành động cho người dùng dễ đọc
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
            
            # Sử dụng hàm render_aggrid có sẵn của dự án để chuẩn hóa UI
            render_aggrid(display_logs, key="accounting_audit_trail_logs_grid")