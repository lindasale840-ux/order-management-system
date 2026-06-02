from repositories.document_tracking_repository import (
    DocumentTrackingRepository
)

from repositories.log_repository import (
    LogRepository
)


class DocumentTrackingService:

    @staticmethod
    def add_tracking(

        order_number,

        sent_date,

        received_date,

        note

    ):

        DocumentTrackingRepository.add_tracking(

            order_number,

            sent_date,

            received_date,

            note
        )

        LogRepository.add_log(

            "ADD_DOCUMENT_TRACKING",

            "",

            order_number,

            f"""

            sent_date={sent_date}

            received_date={received_date}

            note={note}

            """
        )

    @staticmethod
    def delete_tracking(
        tracking_id
    ):

        DocumentTrackingRepository.delete_tracking(
            tracking_id
        )

        LogRepository.add_log(

            "DELETE_DOCUMENT_TRACKING",

            "",

            "",

            f"id={tracking_id}"
        )