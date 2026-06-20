import streamlit as st
import pandas as pd
import os
from sqlalchemy import text
from datetime import datetime
from database.connection import engine

# Tạo thư mục lưu trữ file vật lý tập trung nếu chưa có nhằm tối ưu hiệu năng DB
UPLOAD_DIR = "storage_files"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# ========================================================
# DATA ACCESS LAYER
# ========================================================
def get_template(template_type, lang_type):
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT content FROM document_templates WHERE template_type = :t AND language_type = :l"),
            {"t": template_type, "l": lang_type}
        ).fetchone()
        return result[0] if result else "<h3>Chưa có dữ liệu biểu mẫu</h3>"

def save_template(template_type, lang_type, content):
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE document_templates SET content = :c, updated_at = CURRENT_TIMESTAMP WHERE template_type = :t AND language_type = :l"),
            {"c": content, "t": template_type, "l": lang_type}
        )

# ========================================================
# MAIN INTERFACE
# ========================================================
def show_document_template_page():
    st.title("📝 Smart Document & Template Hub")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📄 Hợp đồng Song ngữ",
        "💰 Đề nghị thanh toán",
        "📜 Hồ sơ thầu & ISO",
        "📂 Kho Biểu Mẫu Kinh Doanh"
    ])

    # Bộ soạn thảo HTML/PDF Editor
    def render_smart_editor(current_content, key_suffix, filename_pdf):
        editor_html = f"""
        <link href="https://cdn.jsdelivr.net/npm/quill@2.0.2/dist/quill.snow.css" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/quill@2.0.2/dist/quill.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
        <div style="background: white; border-radius: 8px; padding: 5px;">
            <div id="quill_editor_{key_suffix}" style="height: 380px; font-size: 15px; color: #000000;">{current_content}</div>
        </div>
        <script>
        const quill = new Quill('#quill_editor_{key_suffix}', {{
            theme: 'snow', modules: {{ toolbar: [[{{ 'header': [1, 2, 3, false] }}], ['bold', 'italic', 'underline', 'strike'], [{{ 'color': [] }}, {{ 'background': [] }}], [{{ 'list': 'ordered'}}, {{ 'list': 'bullet' }}], ['table', 'align'], ['clean']] }}
        }});
        quill.on('text-change', function() {{
            window.parent.postMessage({{ type: 'streamlit:setComponentValue', value: quill.root.innerHTML }}, '*');
        }});
        function exportToPDF() {{
            html2pdf().set({{ margin: 15, filename: '{filename_pdf}.pdf', image: {{ type: 'jpeg', quality: 0.98 }}, html2canvas: {{ scale: 2, useCORS: true }}, jsPDF: {{ unit: 'mm', format: 'a4', orientation: 'portrait' }} }}).from(quill.root).save();
        }}
        </script>
        <button onclick="exportToPDF()" style="width: 100%; margin-top: 10px; padding: 10px; background-color: #ef4444; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">📊 Xuất file và Tải PDF trực tuyến về máy tính</button>
        """
        return st.components.v1.html(editor_html, height=515)

    # --- TAB 1: HỢP ĐỒNG SONG NGỮ ---
    with tab1:
        st.subheader("📋 Quản lý cấu trúc Hợp đồng")
        lang_contract = st.selectbox("Chọn ngôn ngữ hợp đồng:", ["Trung - Việt (ZH-VI)", "Anh - Việt (EN-VI)"], key="sel_lang_c")
        lang_code_c = "zh_vi" if "Trung" in lang_contract else "en_vi"
        c_db_content = get_template("contract", lang_code_c)
        if f"c_buf_{lang_code_c}" not in st.session_state: st.session_state[f"c_buf_{lang_code_c}"] = c_db_content
        res_c = render_smart_editor(st.session_state[f"c_buf_{lang_code_c}"], f"contract_{lang_code_c}", f"Hop_Dong_{lang_code_c.upper()}")
        if res_c is not None and type(res_c) == str and res_c != st.session_state[f"c_buf_{lang_code_c}"]: st.session_state[f"c_buf_{lang_code_c}"] = res_c
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            if st.button("💾 Lưu cấu trúc mẫu", key="btn_s_c", use_container_width=True):
                save_template("contract", lang_code_c, st.session_state[f"c_buf_{lang_code_c}"])
                st.success("🎉 Đã lưu phiên bản vào Database!")
                st.rerun()
        with col_c2:
            st.download_button("📥 Tải file Word (.doc)", data=str(st.session_state[f"c_buf_{lang_code_c}"]), file_name=f"Hop_Dong_{lang_code_c.upper()}.doc", mime="text/html", use_container_width=True)

    # --- TAB 2: ĐỀ NGHỊ THANH TOÁN ---
    with tab2:
        st.subheader("📋 Quản lý Đề nghị thanh toán")
        lang_payment = st.selectbox("Chọn ngôn ngữ đề nghị:", ["Trung - Việt (ZH-VI)", "Anh - Việt (EN-VI)"], key="sel_lang_p")
        lang_code_p = "zh_vi" if "Trung" in lang_payment else "en_vi"
        p_db_content = get_template("payment_request", lang_code_p)
        if f"p_buf_{lang_code_p}" not in st.session_state: st.session_state[f"p_buf_{lang_code_p}"] = p_db_content
        res_p = render_smart_editor(st.session_state[f"p_buf_{lang_code_p}"], f"payment_{lang_code_p}", f"De_Nghi_Thanh_Toan_{lang_code_p.upper()}")
        if res_p is not None and type(res_p) == str and res_p != st.session_state[f"p_buf_{lang_code_p}"]: st.session_state[f"p_buf_{lang_code_p}"] = res_p
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            if st.button("💾 Lưu cấu trúc mẫu", key="btn_s_p", use_container_width=True):
                save_template("payment_request", lang_code_p, st.session_state[f"p_buf_{lang_code_p}"])
                st.success("🎉 Đã lưu biểu mẫu thành công!")
                st.rerun()
        with col_p2:
            st.download_button("📥 Tải file Word (.doc)", data=str(st.session_state[f"p_buf_{lang_code_p}"]), file_name=f"De_Nghi_Thanh_Toan_{lang_code_p.upper()}.doc", mime="text/html", use_container_width=True)

    # --- TAB 3: HỒ SƠ THẦU & ISO (BẮT BUỘC ĐIỀN ĐẦY ĐỦ THÔNG TIN) ---
    with tab3:
        st.subheader("📜 Quản lý Năng lực Nhà thầu & Chứng nhận ISO")
        
        with st.expander("➕ Tải lên Hồ sơ Nhà thầu Mới", expanded=True):
            with st.form("form_add_cert", clear_on_submit=False): # Giữ lại thông tin cũ để người dùng sửa nếu lỗi
                in_name = st.text_input("Tên chứng nhận / Loại tài liệu (*)")
                in_contractor = st.text_input("Tên nhà thầu / Đối tác (*)")
                in_version = st.text_input("Phiên bản/Mã hiệu (*)", value="V1.0")
                in_date = st.date_input("Ngày hết hạn hiệu lực (*)")
                uploaded_file_cert = st.file_uploader("Chọn tệp tài liệu từ máy tính (*)", key="upload_cert")
                
                if st.form_submit_button("⚡ Xác nhận Tải lên & Lưu hệ thống", use_container_width=True):
                    # --- BỘ CHẶN LỖI BÁO ĐỎ TẤT CẢ CÁC TRƯỜNG ---
                    if not in_name.strip():
                        st.error("❌ Vui lòng nhập 'Tên chứng nhận / Loại tài liệu'!")
                    elif not in_contractor.strip():
                        st.error("❌ Vui lòng nhập 'Tên nhà thầu / Đối tác'!")
                    elif not in_version.strip():
                        st.error("❌ Vui lòng nhập 'Phiên bản/Mã hiệu'!")
                    elif uploaded_file_cert is None:
                        st.error("❌ Vui lòng chọn tệp tài liệu tải lên từ máy tính!")
                    else:
                        # Hợp lệ -> Tiến hành lưu tệp vật lý
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        safe_filename = f"cert_{timestamp}_{uploaded_file_cert.name}"
                        file_save_path = os.path.join(UPLOAD_DIR, safe_filename)
                        
                        with open(file_save_path, "wb") as f:
                            f.write(uploaded_file_cert.getbuffer())
                        
                        with engine.begin() as conn:
                            conn.execute(
                                text("""INSERT INTO erp_certificates (cert_name, contractor_name, version, expiry_date, file_path, file_name) 
                                     VALUES (:n, :c, :v, :d, :path, :orig_name)"""),
                                {"n": in_name.strip(), "c": in_contractor.strip(), "v": in_version.strip(), "d": str(in_date), "path": file_save_path, "orig_name": uploaded_file_cert.name}
                            )
                        st.success("✨ Đã lưu thông tin và tải tệp lên hệ thống thành công!")
                        st.rerun()
        
        with engine.connect() as conn:
            df_certs = pd.read_sql_query(text("SELECT id, cert_name, contractor_name, version, expiry_date, file_path, file_name FROM erp_certificates"), conn)
        
        if df_certs.empty:
            st.info("Hiện tại chưa có hồ sơ nào.")
        else:
            for _, row in df_certs.iterrows():
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([5, 3, 2, 2])
                    with c1:
                        st.markdown(f"📂 **{row['cert_name']}**")
                        st.markdown(f"🏢 Nhà thầu: *{row['contractor_name']}* | File: `{row['file_name']}`")
                    with c2:
                        exp_date = datetime.strptime(row['expiry_date'], "%Y-%m-%d").date()
                        days_left = (exp_date - pd.Timestamp.today().date()).days
                        if days_left < 0: st.error(f"🚨 Đã quá hạn ({abs(days_left)} ngày)")
                        elif days_left < 180: st.warning(f"⚠️ Sắp hết hạn ({days_left} ngày)")
                        else: st.success(f"✅ Còn hạn ({days_left} ngày)")
                    with c3:
                        if row['file_path'] and os.path.exists(row['file_path']):
                            with open(row['file_path'], "rb") as f:
                                st.download_button("📥 Tải file", data=f.read(), file_name=row['file_name'], key=f"dl_cert_{row['id']}", use_container_width=True)
                        else:
                            st.error("Không tìm thấy file")
                    with c4:
                        if st.button("❌ Xóa", key=f"del_cert_{row['id']}", use_container_width=True):
                            if row['file_path'] and os.path.exists(row['file_path']):
                                os.remove(row['file_path'])
                            with engine.begin() as conn:
                                conn.execute(text("DELETE FROM erp_certificates WHERE id = :id"), {"id": row['id']})
                            st.toast("🗑️ Đã xóa hồ sơ thành công!")
                            st.rerun()

    # --- TAB 4: KHO BIỂU MẪU KINH DOANH (BẮT BUỘC ĐIỀN ĐẦY ĐỦ THÔNG TIN) ---
    with tab4:
        st.subheader("📂 Kho Biểu Mẫu Nghiệp Vụ - Phòng Kinh Doanh")
        
        with st.expander("➕ Tải lên Biểu mẫu Văn bản Mới", expanded=True):
            with st.form("form_add_biz_form", clear_on_submit=False):
                f_name = st.text_input("Tên văn bản mẫu (*)")
                f_desc = st.text_area("Mô tả công năng (*)")
                uploaded_file_biz = st.file_uploader("Chọn tệp biểu mẫu từ máy tính (*)", key="upload_biz")
                
                if st.form_submit_button("💾 Lưu kho tài nguyên", use_container_width=True):
                    # --- BỘ CHẶN LỖI BÁO ĐỎ TẤT CẢ CÁC TRƯỜNG ---
                    if not f_name.strip():
                        st.error("❌ Vui lòng nhập 'Tên văn bản mẫu'!")
                    elif not f_desc.strip():
                        st.error("❌ Vui lòng nhập thông tin 'Mô tả công năng'!")
                    elif uploaded_file_biz is None:
                        st.error("❌ Vui lòng chọn tệp biểu mẫu tải lên từ máy tính!")
                    else:
                        # Hợp lệ -> Lưu file vật lý
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        safe_filename = f"biz_{timestamp}_{uploaded_file_biz.name}"
                        file_save_path = os.path.join(UPLOAD_DIR, safe_filename)
                        
                        with open(file_save_path, "wb") as f:
                            f.write(uploaded_file_biz.getbuffer())
                            
                        with engine.begin() as conn:
                            conn.execute(
                                text("""INSERT INTO erp_business_forms (form_name, description, file_path, file_name) 
                                     VALUES (:n, :d, :path, :orig_name)"""),
                                {"n": f_name.strip(), "d": f_desc.strip(), "path": file_save_path, "orig_name": uploaded_file_biz.name}
                            )
                        st.success("Đã ghi nhận biểu mẫu mới vào hệ thống vật lý!")
                        st.rerun()

        with engine.connect() as conn:
            df_biz = pd.read_sql_query(text("SELECT id, form_name, description, file_path, file_name FROM erp_business_forms"), conn)

        if df_biz.empty:
            st.info("Kho biểu mẫu đang trống.")
        else:
            for _, row in df_biz.iterrows():
                with st.container(border=True):
                    b1, b2, b3 = st.columns([7, 3, 2])
                    with b1:
                        st.markdown(f"📄 **{row['form_name']}**")
                        st.caption(f"Mô tả: {row['description']} | Tệp: `{row['file_name']}`")
                    with b2:
                        if row['file_path'] and os.path.exists(row['file_path']):
                            with open(row['file_path'], "rb") as f:
                                st.download_button("📥 Tải về máy", data=f.read(), file_name=row['file_name'], key=f"dl_biz_{row['id']}", use_container_width=True)
                        else:
                            st.error("Không thấy file")
                    with b3:
                        if st.button("❌ Xóa", key=f"del_biz_{row['id']}", use_container_width=True):
                            if row['file_path'] and os.path.exists(row['file_path']):
                                os.remove(row['file_path'])
                            with engine.begin() as conn:
                                conn.execute(text("DELETE FROM erp_business_forms WHERE id = :id"), {"id": row['id']})
                            st.toast("🗑️ Đã xóa biểu mẫu thành công!")
                            st.rerun()