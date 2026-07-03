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

        note,
        
        created_by,   # 1. Nhận thêm biến này từ Giao diện gửi vào
        sale_owner    # 2. Nhận thêm biến này từ Giao diện gửi vào

    ):

        OtherDocumentTrackingRepository.add_tracking(

            customer_name,

            document_type,

            sent_date,

            received_date,

            note,
            
            created_by,   # 3. Truyền tiếp xuống Repository
            sale_owner    # 4. Truyền tiếp xuống Repository

        )

    @staticmethod
    def delete_tracking(record_id):

        OtherDocumentTrackingRepository.delete_tracking(
            record_id
        )