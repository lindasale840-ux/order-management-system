import streamlit as st
import pandas as pd
import plotly.express as px
import io  # Sử dụng để xuất file Excel mà không cần lưu xuống đĩa

from services.finance_service import (
    FinanceService
)

from repositories.order_repository import (
    OrderRepository
)

from components.aggrid_table import (
    render_aggrid
)

def show_chart_customer_page():
    st.title("📈 Analytics Dashboard")

    # =========================
    # LOAD DATA
    # =========================
    df = FinanceService.build_finance_dataframe(
        role=st.session_state.get("role"),
        username=st.session_state.get("username"),
        sale_owner=st.session_state.get("sale_owner")
    )

    if df.empty:
        st.warning("No data found")
        return

    # Định dạng lại cột ngày tháng trước để phục vụ cho bộ lọc ngày
    df["invoice_date"] = pd.to_datetime(df["invoice_date"], errors="coerce")

    # ==================================================
    # ⚙️ KHU VỰC BỘ LỌC ĐẦU TRANG (ADVANCED FILTER HEADER)
    # ==================================================
    with st.container(border=True):
        st.markdown("#### 🔍 Advanced Filters")
        
        # Tạo layout 3 cột bằng nhau cho các bộ lọc chính
        f_col1, f_col2, f_col3 = st.columns(3)
        
        with f_col1:
            # 1. Ô tìm kiếm nhanh tên khách hàng (Gõ để thu hẹp phạm vi)
            search_query = st.text_input("✍️ Type to search Customer Name", "", placeholder="Enter keyword...")

        # Xử lý danh sách khách hàng dựa trên ô tìm kiếm
        customer_df = OrderRepository.get_customers()
        all_customers = customer_df["customer_name"].dropna().unique().tolist()
        
        if search_query:
            # Lọc danh sách dropdown chỉ giữ lại những tên chứa từ khóa (không phân biệt hoa thường)
            filtered_options = [cust for cust in all_customers if search_query.lower() in cust.lower()]
        else:
            filtered_options = all_customers

        # Thêm lựa chọn "ALL" vào đầu danh sách
        customer_options = ["ALL"] + filtered_options

        with f_col2:
            # 2. Dropdown động - giờ đây danh sách này đã ngắn hơn rất nhiều nhờ ô tìm kiếm phía trên
            selected_customer = st.selectbox("🎯 Select Customer from List", customer_options)

        with f_col3:
            # 3. Bộ lọc khoảng ngày (Date Range Filter)
            min_date = df["invoice_date"].min() if not df["invoice_date"].empty else pd.Timestamp.today()
            max_date = df["invoice_date"].max() if not df["invoice_date"].empty else pd.Timestamp.today()
            
            date_range = st.date_input(
                "📅 Invoice Date Range",
                value=(min_date.date(), max_date.date()),
                min_value=min_date.date(),
                max_value=max_date.date()
            )

    # ==================================================
    # ⚡ THỰC THI LỌC DỮ LIỆU (DATA FILTERING LOGIC)
    # ==================================================
    # Lọc theo Khách hàng được chọn
    if selected_customer != "ALL":
        df = df[df["customer_name"] == selected_customer]
    elif search_query and not filtered_options:
        # Nếu gõ từ khóa tìm kiếm nhưng không ra kết quả nào khớp
        df = df[df["id"] == -1] # Trả về df rỗng một cách an toàn

    # Lọc theo Khoảng ngày (chỉ chạy khi người dùng chọn đủ ngày bắt đầu và ngày kết thúc)
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        df = df[(df["invoice_date"].dt.date >= start_date) & (df["invoice_date"].dt.date <= end_date)]

    # Nếu sau khi lọc, dữ liệu trống, thông báo cho người dùng
    if df.empty:
        st.info("No records match the selected filters.")
        return

    # ==================================================
    # 📊 KHU VỰC THẺ TỔNG HỢP SỐ LIỆU (KPI CARDS) + NÚT XUẤT EXCEL
    # ==================================================
    # Tính toán các chỉ số dựa trên dữ liệu ĐÃ LỌC
    total_revenue = df["total"].sum()
    total_invoices = df.shape[0]
    
    # Tính tổng tiền thực tế đã thanh toán (Paid)
    total_paid = df[df["payment_status_text"] == "Paid"]["total"].sum() if "payment_status_text" in df.columns else 0

    # Tạo hàng hiển thị KPI và nút Xuất File
    kpi_col1, kpi_col2, kpi_col3, kpi_btn = st.columns([1, 1, 1, 1])

    with kpi_col1:
        with st.container(border=True):
            st.metric(label="Total Revenue", value=f"${total_revenue:,.2f}")
    with kpi_col2:
        with st.container(border=True):
            st.metric(label="Total Invoices", value=f"{total_invoices:,}")
    with kpi_col3:
        with st.container(border=True):
            st.metric(label="Actual Paid Amount", value=f"${total_paid:,.2f}")
            
    with kpi_btn:
        # Thiết lập nút xuất file Excel sử dụng thư viện pandas và openpyxl (hoặc xlsxwriter) mặc định của pandas
        st.write("") # Tạo khoảng trống canh lề dọc cho đẹp với thẻ Metric
        st.write("") 
        
        # Chuyển đổi DataFrame hiện tại thành nhị phân Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            # Tạo bản sao đổi tên cột hoặc định dạng lại ngày tháng để xuất file Excel đẹp hơn nếu cần
            export_df = df.copy()
            if "invoice_date" in export_df.columns:
                export_df["invoice_date"] = export_df["invoice_date"].dt.strftime('%Y-%m-%d')
            export_df.to_excel(writer, sheet_name='Analytics_Data', index=False)
            
        st.download_button(
            label="📥 Export to Excel",
            data=buffer.getvalue(),
            file_name="ERP_Analytics_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    # ==================================================
    # TABS (Phần đồ thị giữ nguyên phong cách ERP đã tối ưu trước đó)
    # ==================================================
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Revenue Trend",
        "🏆 Customer Analytics",
        "💰 Payment Analytics",
        "📜 Certificate Analytics"
    ])

    COLOR_THEME_LINE = px.colors.diverging.Tealrose
    COLOR_THEME_BAR = px.colors.qualitative.Prism
    COLOR_THEME_PIE = px.colors.qualitative.Safe

    # --- TAB 1: REVENUE TREND ---
    with tab1:
        revenue_df = df.dropna(subset=["invoice_date"]).copy()

        if not revenue_df.empty:
            revenue_df["year_month"] = revenue_df["invoice_date"].dt.strftime("%Y-%m")

            col_trend_left, col_trend_right = st.columns([1, 1])

            with col_trend_left:
                with st.container(border=True):
                    st.markdown("#### Monthly Revenue Trend")
                    monthly_revenue = revenue_df.groupby("year_month")["total"].sum().reset_index()
                    
                    fig = px.line(
                        monthly_revenue, x="year_month", y="total", markers=True,
                        color_discrete_sequence=COLOR_THEME_LINE
                    )
                    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=320, hovermode="x unified")
                    st.plotly_chart(fig, use_container_width=True)

            with col_trend_right:
                with st.container(border=True):
                    st.markdown("#### Monthly Paid Revenue")
                    paid_df = revenue_df[revenue_df["payment_status_text"] == "Paid"]
                    
                    if not paid_df.empty:
                        paid_chart = paid_df.groupby("year_month")["total"].sum().reset_index()
                        paid_chart["year_month"] = paid_chart["year_month"].astype(str)

                        fig_bar = px.bar(
                            paid_chart, x="year_month", y="total",
                            color="total", color_continuous_scale="Viridis"
                        )
                        fig_bar.update_xaxes(type="category")
                        fig_bar.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=320, coloraxis_showscale=False)
                        st.plotly_chart(fig_bar, use_container_width=True)
                    else:
                        st.info("No paid revenue data available for this selection.")

            with st.container(border=True):
                st.markdown("#### Detailed Monthly Revenue Data")
                render_aggrid(
                    monthly_revenue,
                    height=280,
                    page_size=12,
                    key="revenue_trend_by_month"
                )

    # --- TAB 2: CUSTOMER ANALYTICS ---
    with tab2:
        customer_chart = df.groupby("customer_name")["total"].sum().reset_index()
        customer_chart = customer_chart.sort_values("total", ascending=False)
        top10 = customer_chart.head(10)

        col_cust_left, col_cust_right = st.columns([6, 4])

        with col_cust_left:
            with st.container(border=True):
                st.markdown("#### Revenue Distribution By Customer")
                fig_cust = px.bar(
                    customer_chart, x="customer_name", y="total",
                    color="total", color_continuous_scale="Plasma"
                )
                fig_cust.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=380, coloraxis_showscale=False)
                st.plotly_chart(fig_cust, use_container_width=True)

        with col_cust_right:
            with st.container(border=True):
                st.markdown("#### 🏆 Top 10 Customers Leaderboard")
                render_aggrid(
                    top10,
                    height=380,
                    page_size=10,
                    key="top_10_customers"
                )

    # --- TAB 3: PAYMENT ANALYTICS ---
    with tab3:
        col_pay_left, col_pay_right = st.columns([1, 1])

        with col_pay_left:
            with st.container(border=True):
                st.markdown("#### Payment Status Distribution")
                payment_summary = df["payment_status_text"].value_counts().reset_index()
                payment_summary.columns = ["status", "count"]

                fig_pay_pie = px.pie(
                    payment_summary, names="status", values="count",
                    hole=0.4, color_discrete_sequence=COLOR_THEME_PIE
                )
                fig_pay_pie.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=340, legend=dict(orientation="h", y=-0.1))
                st.plotly_chart(fig_pay_pie, use_container_width=True)

        with col_pay_right:
            with st.container(border=True):
                st.markdown("#### Overdue Analysis Status")
                overdue_df = df["payment_overdue"].value_counts().reset_index()
                overdue_df.columns = ["status", "count"]

                fig_pay_bar = px.bar(
                    overdue_df, x="status", y="count",
                    color="status", color_discrete_sequence=COLOR_THEME_BAR
                )
                fig_pay_bar.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=340, showlegend=False)
                st.plotly_chart(fig_pay_bar, use_container_width=True)

    # --- TAB 4: CERTIFICATE ANALYTICS ---
    with tab4:
        with st.container(border=True):
            st.markdown("#### Certificate Workflow Status Overview")
            cert_df = df["cert_workflow_status"].value_counts().reset_index()
            cert_df.columns = ["status", "count"]

            fig_cert_pie = px.pie(
                cert_df, names="status", values="count",
                hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_cert_pie.update_layout(margin=dict(l=10, r=10, t=10, b=40), height=300)
            st.plotly_chart(fig_cert_pie, use_container_width=True)

        col_cert_left, col_cert_right = st.columns([1, 1])

        with col_cert_left:
            with st.container(border=True):
                st.markdown("#### ⏳ Calibration Due Soon")
                due_soon_df = df["cert_due_soon"].value_counts().reset_index()
                due_soon_df.columns = ["status", "count"]

                fig_due = px.bar(
                    due_soon_df, x="status", y="count",
                    color="status", color_discrete_sequence=["#F39C12", "#F1C40F"]
                )
                fig_due.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=280, showlegend=False)
                st.plotly_chart(fig_due, use_container_width=True)

        with col_cert_right:
            with st.container(border=True):
                st.markdown("#### 🚨 Calibration Overdue")
                overdue_cert_df = df["cert_overdue"].value_counts().reset_index()
                overdue_cert_df.columns = ["status", "count"]

                fig_overdue = px.bar(
                    overdue_cert_df, x="status", y="count",
                    color="status", color_discrete_sequence=["#E74C3C", "#C0392B"]
                )
                fig_overdue.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=280, showlegend=False)
                st.plotly_chart(fig_overdue, use_container_width=True)