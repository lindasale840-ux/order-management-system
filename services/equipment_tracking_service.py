from repositories.equipment_tracking_repository import (
    EquipmentTrackingRepository
)

from repositories.log_repository import (
    LogRepository
)


class EquipmentTrackingService:

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

        EquipmentTrackingRepository.add_tracking(

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

        LogRepository.add_log(

            "ADD_EQUIPMENT_TRACKING",

            "",

            order_number,

            f"""
            service_type={service_type}
            subcontract={subcontract_name}
            """
        )


    @staticmethod
    def delete_tracking(
        tracking_id
    ):

        EquipmentTrackingRepository.delete_tracking(
            tracking_id
        )

        LogRepository.add_log(

            "DELETE_EQUIPMENT_TRACKING",

            "",

            "",

            f"id={tracking_id}"
        )     