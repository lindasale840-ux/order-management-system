from repositories.other_revenue_repository import OtherRevenueRepository
from repositories.log_repository import LogRepository

class OtherRevenueService:

    @staticmethod
    def add_revenue(revenue_date, amount, note, current_user="Admin"):
        # 1. Gọi Repository để lưu vào bảng doanh thu khác
        OtherRevenueRepository.add_revenue(
            revenue_date,
            amount,
            note,
            current_user=current_user
        )

        # 2. Ghi nhật ký hệ thống: Đưa tên user vào vị trí số 2 (Thường là cột username trong hàm log)
        # Đồng thời lưu vết rõ ràng trong chuỗi nội dung chi tiết để làm căn cứ tính KPI
        LogRepository.add_log(
            "ADD_OTHER_REVENUE",
            current_user,  # Đưa user vào đây để biết ai làm
            "",
            f"""
            Created_by={current_user}
            revenue_date={revenue_date}
            amount={amount}
            note={note}
            """
        )

    @staticmethod
    def delete_revenue(revenue_id, current_user="Admin"):
        OtherRevenueRepository.delete_revenue(
            revenue_id
        )

        LogRepository.add_log(
            "DELETE_OTHER_REVENUE",
            current_user,  # Đưa user vào đây khi xóa
            "",
            f"User {current_user} deleted revenue id={revenue_id}"
        )