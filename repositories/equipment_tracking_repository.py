import pandas as pd
import streamlit as st

from sqlalchemy import text

from database.connection import engine

from utils.datetime_utils import convert_utc_columns

class EquipmentTrackingRepository:

    @staticmethod
    @st.cache_data(ttl=30)
    def get_all():

        query = """

        SELECT *

        FROM equipment_tracking

        ORDER BY id DESC

        """

        df = pd.read_sql(
            query,
            engine
        )
        
        return convert_utc_columns(df)

    @staticmethod
    def add_tracking(

        order_number,

        service_type,

        direct_to_customer,

        subcontract_name,

        customer_send_date,

        gst_receive_date,

        gst_send_sub_date,

        sub_receive_date,

        sub_send_date,

        gst_receive_back_date,

        gst_send_customer_date,

        customer_receive_date,

        note
    ):

        with engine.begin() as conn:

            conn.execute(text("""

            INSERT INTO equipment_tracking (

                order_number,

                service_type,

                direct_to_customer,

                subcontract_name,

                customer_send_date,

                gst_receive_date,

                gst_send_sub_date,

                sub_receive_date,

                sub_send_date,

                gst_receive_back_date,

                gst_send_customer_date,

                customer_receive_date,

                note

            )

            VALUES (

                :order_number,

                :service_type,

                :direct_to_customer,

                :subcontract_name,

                :customer_send_date,

                :gst_receive_date,

                :gst_send_sub_date,

                :sub_receive_date,

                :sub_send_date,

                :gst_receive_back_date,

                :gst_send_customer_date,

                :customer_receive_date,

                :note

            )

            """),

            {

                "order_number": order_number,

                "service_type": service_type,

                "direct_to_customer": direct_to_customer,

                "subcontract_name": subcontract_name,

                "customer_send_date": customer_send_date,

                "gst_receive_date": gst_receive_date,

                "gst_send_sub_date": gst_send_sub_date,

                "sub_receive_date": sub_receive_date,

                "sub_send_date": sub_send_date,

                "gst_receive_back_date": gst_receive_back_date,

                "gst_send_customer_date": gst_send_customer_date,

                "customer_receive_date": customer_receive_date,

                "note": note

            })

        st.cache_data.clear()


    @staticmethod
    def delete_tracking(
        tracking_id
    ):

        with engine.begin() as conn:

            conn.execute(

                text("""

                DELETE FROM equipment_tracking

                WHERE id=:id

                """),

                {

                    "id": tracking_id
                }
            )

        st.cache_data.clear()    


    @staticmethod
    @st.cache_data(ttl=30)
    def get_tracking_dashboard():

        query = """

        SELECT *

        FROM equipment_tracking

        ORDER BY id DESC

        """

        df = pd.read_sql(
            query,
            engine
        )  
        
        return convert_utc_columns(df)  
    
    @staticmethod
    def tracking_exists(
        order_number
    ):

        query = text("""

        SELECT COUNT(*)

        FROM equipment_tracking

        WHERE order_number=:order_number

        """)

        with engine.begin() as conn:

            return conn.execute(

                query,

                {
                    "order_number": order_number
                }

            ).scalar() > 0
        

    @staticmethod
    def update_tracking(

        order_number,

        service_type,

        direct_to_customer,

        subcontract_name,

        customer_send_date,

        gst_receive_date,

        gst_send_sub_date,

        sub_receive_date,

        sub_send_date,

        gst_receive_back_date,

        gst_send_customer_date,

        customer_receive_date,

        note

    ):

        with engine.begin() as conn:

            conn.execute(text("""

            UPDATE equipment_tracking

            SET

                service_type=:service_type,

                direct_to_customer=:direct_to_customer,

                subcontract_name=:subcontract_name,

                customer_send_date=:customer_send_date,

                gst_receive_date=:gst_receive_date,

                gst_send_sub_date=:gst_send_sub_date,

                sub_receive_date=:sub_receive_date,

                sub_send_date=:sub_send_date,

                gst_receive_back_date=:gst_receive_back_date,

                gst_send_customer_date=:gst_send_customer_date,

                customer_receive_date=:customer_receive_date,

                note=:note

            WHERE order_number=:order_number

            """),

            {

                "order_number": order_number,

                "service_type": service_type,

                "direct_to_customer": direct_to_customer,

                "subcontract_name": subcontract_name,

                "customer_send_date": customer_send_date,

                "gst_receive_date": gst_receive_date,

                "gst_send_sub_date": gst_send_sub_date,

                "sub_receive_date": sub_receive_date,

                "sub_send_date": sub_send_date,

                "gst_receive_back_date": gst_receive_back_date,

                "gst_send_customer_date": gst_send_customer_date,

                "customer_receive_date": customer_receive_date,

                "note": note

            })

        st.cache_data.clear() 

    @staticmethod
    def get_by_order_number(
        order_number
    ):

        query = """

        SELECT *

        FROM equipment_tracking

        WHERE order_number=:order_number

        LIMIT 1

        """

        df = pd.read_sql(

            text(query),

            engine,

            params={
                "order_number": order_number
            }

        )  
        
        return convert_utc_columns(df)     