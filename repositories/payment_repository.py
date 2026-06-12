import pandas as pd
import streamlit as st

from sqlalchemy import text

from database.connection import engine

from utils.datetime_utils import convert_utc_columns


class PaymentRepository:

    @staticmethod
    @st.cache_data(ttl=30)

    def get_all_payments():

        query = """

        SELECT *

        FROM payments

        ORDER BY id DESC

        """

        df =  pd.read_sql(
            query,
            engine
        )
        
        return convert_utc_columns(df)

    @staticmethod
    def upsert_payment(

        order_number,

        invoice_date,

        invoice_group,

        payment_terms,

        payment_status,

        total,

        commission_percent,

        commission_actual,

        note,
        
        invoice_created_by
    ):

        with engine.begin() as conn:

            conn.execute(text("""

            INSERT INTO payments (

                order_number,

                invoice_date,
                              
                invoice_group,              

                payment_terms,

                payment_status,

                total,

                commission_percent,

                commission_actual,

                note,
                
                invoice_created_by

            )

            VALUES (

                :order_number,

                :invoice_date,
                              
                :invoice_group,             

                :payment_terms,

                :payment_status,

                :total,

                :commission_percent,

                :commission_actual,

                :note,
                
                :invoice_created_by
            )

            ON CONFLICT(order_number)

            DO UPDATE SET

                invoice_date=excluded.invoice_date,
                              
                invoice_group=excluded.invoice_group,              

                payment_terms=excluded.payment_terms,

                payment_status=excluded.payment_status,

                total=excluded.total,

                commission_percent=excluded.commission_percent,

                commission_actual=excluded.commission_actual,

                note=excluded.note,
                
                invoice_created_by=excluded.invoice_created_by,

                updated_at=CURRENT_TIMESTAMP

            """),

            {

                "order_number": order_number,

                "invoice_date": invoice_date,

                "invoice_group": invoice_group,

                "payment_terms": payment_terms,

                "payment_status": payment_status,

                "total": total,

                "commission_percent": commission_percent,

                "commission_actual": commission_actual,

                "note": note,
                
                "invoice_created_by": invoice_created_by
            })

        st.cache_data.clear()
        
    
    @staticmethod
    def bulk_transfer_invoice_owner(
        old_owner,
        new_owner
    ):

        with engine.begin() as conn:

            conn.execute(

                text("""

                UPDATE payments

                SET invoice_created_by = :new_owner

                WHERE invoice_created_by = :old_owner

                """),

                {

                    "old_owner": old_owner,

                    "new_owner": new_owner

                }

            )

        st.cache_data.clear()  
        
    @staticmethod
    def transfer_invoice_owner_by_orders(

        order_numbers,

        new_assistant

    ):

        if not order_numbers:

            return

        placeholders = ",".join(

            [f":p{i}" for i in range(len(order_numbers))]

        )

        params = {

            f"p{i}": order_numbers[i]

            for i in range(len(order_numbers))

        }

        params["new_assistant"] = new_assistant

        with engine.begin() as conn:

            conn.execute(

                text(f"""

                UPDATE payments

                SET invoice_created_by = :new_assistant

                WHERE order_number IN ({placeholders})

                """),

                params

            )

        st.cache_data.clear()      