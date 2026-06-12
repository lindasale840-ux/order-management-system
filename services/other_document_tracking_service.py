from repositories.other_document_tracking_repository import (
    OtherDocumentTrackingRepository
)


class OtherDocumentTrackingService:

    @staticmethod
    def add_tracking(

        customer_name,

        document_type,

        sent_date,

        received_date,

        note

    ):

        OtherDocumentTrackingRepository.add_tracking(

            customer_name,

            document_type,

            sent_date,

            received_date,

            note

        )

    @staticmethod
    def delete_tracking(record_id):

        OtherDocumentTrackingRepository.delete_tracking(
            record_id
        )