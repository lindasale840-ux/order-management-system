from repositories.equipment_tracking_repository import (
    EquipmentTrackingRepository
)

from utils.business_day import (
    working_days_between
)


class EquipmentTrackingNotificationService:

    @staticmethod
    def get_alert_count():

        tracking_df = (
            EquipmentTrackingRepository
            .get_all()
        )

        if tracking_df.empty:

            return 0

        total_alert = 0

        for _, row in tracking_df.iterrows():

            working_days = working_days_between(

                row["customer_send_date"],

                row["customer_receive_date"]

            )

            if working_days is None:

                continue

            if (

                row["service_type"] == "LAB"

                and

                working_days > 3

            ):

                total_alert += 1

            elif (

                row["service_type"] == "SUBCONTRACT_LAB"

                and

                working_days > 7

            ):

                total_alert += 1

        return total_alert