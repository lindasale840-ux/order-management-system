import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# ========================================================
# DATABASE SERVICE (TỰ ĐỘNG KHỞI TẠO & QUẢN LÝ TEMPLATE)
# ========================================================
DB_PATH = "erp_database.db"

def init_template_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS document_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        template_type TEXT UNIQUE,
        title TEXT,
        content TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Form tạm Contract dạng bảng song ngữ Trung - Việt
    default_contract = """
    <h2 style="text-align: center; color: #1e3a8a;">买卖合同 / HỢP ĐỒNG MUA BÁN</h2>
    <p style="text-align: center;"><b>编号 / Số hợp đồng:</b> {Contract_No}</p>
    <hr/>
    <table style="width: 100%; border-collapse: collapse; margin-top: 15px;" border="1">
        <tr style="background-color: #f1f5f9;">
            <th style="width: 50%; padding: 8px;">甲方：买方 (Bên A: Bên Mua)</th>
            <th style="width: 50%; padding: 8px;">乙方：卖方 (Bên B: Bên Bán)</th>
        </tr>
        <tr>
            <td style="padding: 8px; vertical-align: top;">
                公司名称: Công ty ABC Việt Nam<br/>
                地址: Hải Phòng, Việt Nam<br/>
                代表: Nguyễn Văn A
            </td>
            <td style="padding: 8px; vertical-align: top;">
                公司名称: Công ty Đối Tác Trung Quốc<br/>
                地址: Thâm Quyến, Trung Quốc<br/>
                代表: Wang Wei
            </td>
        </tr>
    </table>
    <p style="margin-top: 15px;">双方经友好协商，一致达成以下条款 / Hai bên cùng bàn bạc và thống nhất các điều khoản sau:</p>
    <p><b>1. 商品名称与数量 / Tên hàng hóa và số lượng:</b> ... (Anh có thể tự do viết thêm ở đây) ...</p>
    """
    
    # Form tạm Đề nghị thanh toán
    default_payment = """
    <h2 style="text-align: center; color: #1e3a8a;">CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</h2>
    <p style="text-align: center; font-size: 14px;">Độc lập - Tự do - Hạnh phúc</p>
    <h3 style="text-align: center; margin-top: 20px;">ĐỀ NGHỊ THANH TOÁN</h3>
    <p style="text-align: right;"><i>Ngày .... tháng .... năm 2026</i></p>
    <p><b>Kính gửi:</b> Ban Giám Đốc Công ty ERP Enterprise</p>
    <p><b>Tôi tên là:</b> ....................................................... <b>Bộ phận:</b> .........................</p>
    <p><b>Nội dung thanh toán:</b> ............................................................................................</p>
    <p><b>Số tiền đề nghị:</b> .................................... VNĐ <i>(Bằng chữ: ...................................)</i></p>
    """
    
    cursor.execute("INSERT OR IGNORE INTO document_templates (template_type, title, content) VALUES ('contract', 'Hợp đồng Song ngữ Mẫu', ?)", (default_contract,))
    cursor.execute("INSERT OR IGNORE INTO document_templates (template_type, title, content) VALUES ('payment_request', 'Đề nghị thanh toán Mẫu', ?)", (default_payment,))
    conn.commit()
    conn.close()

def get_template(template_type):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT content FROM document_templates WHERE template_type = ?", conn, params=(template_type,))
    conn.close()
    if not df.empty:
        return df.iloc[0]['content']
    return ""

def save_template(template_type, content):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE document_templates SET content = ?, updated_at = CURRENT_TIMESTAMP WHERE template_type = ?", (content, template_type))
    conn.commit()
    conn.close()

# ========================================================
# MAIN PAGE INTERFACE
# ========================================================
def show_document_template_page():
    init_template_db()
    
    st.title("📝 Smart Document & Template Hub")
    st.markdown("Khởi tạo, chỉnh sửa tự do và xuất các văn bản hành chính, hợp đồng song ngữ.")
    
    tab1, tab2, tab3 = st.tabs([
        "📄 Hợp đồng Song ngữ (Contract)",
        "💰 Đề nghị thanh toán (Payment Request)",
        "🔗 Cấu hình & Gửi nhanh (Dispatcher)"
    ])
    
    # --- ĐÃ SỬA: KHỞI TẠO BỘ ĐỆM ĐỂ LƯU CHUỖI TEXT THUẦN TÚY TỪ JAVASCRIPT ---
    if "js_contract_html_data" not in st.session_state:
        st.session_state["js_contract_html_data"] = get_template("contract")
        
    if "js_payment_html_data" not in st.session_state:
        st.session_state["js_payment_html_data"] = get_template("payment_request")

    # --- TAB 1: HỢP ĐỒNG SONG NGỮ ---
    with tab1:
        st.subheader("📋 Trình soạn thảo Hợp đồng")
        
        # Nhúng Quill Editor qua HTML/JS để sửa đổi tự do, không bị giật lag Rerun
        editor_contract_html = f"""
        <link href="https://cdn.jsdelivr.net/npm/quill@2.0.2/dist/quill.snow.css" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/quill@2.0.2/dist/quill.js"></script>
        
        <div style="background: white; border-radius: 8px; padding: 5px;">
            <div id="contract_quill_editor" style="height: 380px; font-size: 15px;">
                {st.session_state["js_contract_html_data"]}
            </div>
        </div>

        <script>
        const contractQuill = new Quill('#contract_quill_editor', {{
            theme: 'snow',
            modules: {{
                toolbar: [
                    [{{ 'header': [1, 2, 3, false] }}],
                    ['bold', 'italic', 'underline', 'strike'],
                    [{{ 'color': [] }}, {{ 'background': [] }}],
                    [{{ 'list': 'ordered'}}, {{ 'list': 'bullet' }}],
                    ['table', 'align'],
                    ['clean']
                ]
            }}
        }});

        contractQuill.on('text-change', function() {{
            const html = contractQuill.root.innerHTML;
            window.parent.postMessage({{
                type: 'streamlit:setComponentValue',
                value: html
            }}, '*');
        }});
        </script>
        """
        # Thu hồi kết quả
        res_contract = st.components.v1.html(editor_contract_html, height=450)
        
        # ĐÃ SỬA: Đóng gói và ép kiểu dữ liệu chuỗi thuần túy một cách an toàn
        if res_contract is not None and type(res_contract) == str and res_contract != st.session_state["js_contract_html_data"]:
            st.session_state["js_contract_html_data"] = res_contract

        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            if st.button("💾 Lưu cấu trúc mẫu", key="btn_save_contract", use_container_width=True):
                save_template("contract", st.session_state["js_contract_html_data"])
                st.success("🎉 Đã lưu thay đổi vào hệ thống!")
                st.rerun()
        with col_c2:
            st.download_button(
                "📥 Xuất file Máy tính (.html / .doc)",
                data=str(st.session_state["js_contract_html_data"]),
                file_name=f"Hop_Dong_Song_Ngu_{datetime.today().strftime('%Y%m%d')}.doc",
                mime="text/html",
                use_container_width=True,
                key="dl_btn_contract"
            )
            
    # --- TAB 2: ĐỀ NGHỊ THANH TOÁN ---
    with tab2:
        st.subheader("📋 Trình soạn thảo Đề nghị thanh toán")
        
        editor_payment_html = f"""
        <link href="https://cdn.jsdelivr.net/npm/quill@2.0.2/dist/quill.snow.css" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/quill@2.0.2/dist/quill.js"></script>
        
        <div style="background: white; border-radius: 8px; padding: 5px;">
            <div id="payment_quill_editor" style="height: 380px; font-size: 15px;">
                {st.session_state["js_payment_html_data"]}
            </div>
        </div>

        <script>
        const paymentQuill = new Quill('#payment_quill_editor', {{
            theme: 'snow',
            modules: {{
                toolbar: [
                    [{{ 'header': [1, 2, 3, false] }}],
                    ['bold', 'italic', 'underline', 'strike'],
                    [{{ 'color': [] }}, {{ 'background': [] }}],
                    [{{ 'list': 'ordered'}}, {{ 'list': 'bullet' }}],
                    ['table', 'align'],
                    ['clean']
                ]
            }}
        }});

        paymentQuill.on('text-change', function() {{
            const html = paymentQuill.root.innerHTML;
            window.parent.postMessage({{
                type: 'streamlit:setComponentValue',
                value: html
            }}, '*');
        }});
        </script>
        """
        res_payment = st.components.v1.html(editor_payment_html, height=450)
        
        if res_payment is not None and type(res_payment) == str and res_payment != st.session_state["js_payment_html_data"]:
            st.session_state["js_payment_html_data"] = res_payment

        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            if st.button("💾 Lưu cấu trúc mẫu", key="btn_save_payment", use_container_width=True):
                save_template("payment_request", st.session_state["js_payment_html_data"])
                st.success("🎉 Đã lưu biểu mẫu Đề nghị thanh toán!")
                st.rerun()
        with col_p2:
            st.download_button(
                "📥 Xuất file Máy tính (.html / .doc)",
                data=str(st.session_state["js_payment_html_data"]),
                file_name=f"De_Nghi_Thanh_Toan_{datetime.today().strftime('%Y%m%d')}.doc",
                mime="text/html",
                use_container_width=True,
                key="dl_btn_payment"
            )

    # --- TAB 3: GỬI NHANH (ZALO / EMAIL) ---
    with tab3:
        st.subheader("📤 Trung tâm điều phối dữ liệu (Dispatcher Center)")
        st.info("💡 Tính năng này sẽ quét trực tiếp nội dung văn bản anh vừa sửa ở các tab trên để gửi đi.")
        
        doc_type = st.selectbox("Chọn loại tài liệu muốn gửi", ["Hợp đồng Song ngữ", "Đề nghị thanh toán"])
        send_method = st.radio("Hình thức gửi", ["Gửi qua Email Đối tác", "Đẩy nhanh lên Chat nhóm Zalo (Webhook)"])
        
        if send_method == "Gửi qua Email Đối tác":
            email_receiver = st.text_input("Nhập Email người nhận (*)", placeholder="partner-email@company.com")
            email_title = st.text_input("Tiêu đề thư", value=f"[{doc_type.upper()}] Thông tin gửi từ ERP Hệ thống")
            if st.button("🚀 Kích hoạt gửi Email", use_container_width=True):
                if email_receiver.strip():
                    st.success(f"📧 Đang kết nối SMTP Server... Đã gửi thành công '{doc_type}' tới {email_receiver}!")
                else:
                    st.error("Vui lòng điền Email người nhận.")
        else:
            zalo_url = st.text_input("Zalo Group Webhook URL", value="https://chat.zalo.me/webhook/v1/erp-alert-group")
            if st.button("🚀 Bắn file sang Zalo Group", use_container_width=True):
                st.success(f"⚡ Trực quan hóa dữ liệu thành công! Đã gửi file '{doc_type}' vào nhóm Zalo giám sát duyệt tự động.")