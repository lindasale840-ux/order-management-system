import pandas as pd
import streamlit as st
# Import 2 hàm tiện ích từ file pg_database của bạn
from database.pg_database import query_pg_to_dataframe, execute_pg_query

class RevenueKPIRepository:

    @staticmethod
    @st.cache_data(ttl=30)
    def get_all():
        query = """
        SELECT *
        FROM revenue_kpi
        ORDER BY year DESC
        """
        return query_pg_to_dataframe(query)

    @staticmethod
    def upsert_kpi(year, month, target_amount):
        # Giữ nguyên cú pháp ON CONFLICT thần thánh của bạn, chỉ đổi tên biến thành %s
        query = """
        INSERT INTO revenue_kpi(year, month, target_amount)
        VALUES(%s, %s, %s)
        ON CONFLICT(year, month)
        DO UPDATE SET target_amount = EXCLUDED.target_amount
        """
        
        execute_pg_query(query, (year, month, target_amount))
        
        # Xóa cache của Streamlit sau khi cập nhật dữ liệu để giao diện hiển thị số mới ngay
        st.cache_data.clear()

    @staticmethod
    def get_by_year(year):
        query = "SELECT * FROM revenue_kpi WHERE year = %s"
        return query_pg_to_dataframe(query, (year,))
    
    @staticmethod
    def get_by_year_month(year, month):
        query = "SELECT * FROM revenue_kpi WHERE year = %s AND month = %s"
        return query_pg_to_dataframe(query, (year, month))