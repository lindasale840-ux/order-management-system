from repositories.payment_repository import PaymentRepository

df = PaymentRepository.get_all_payments()

print(
    df[
        [
            "order_number",
            "invoice_created_by"
        ]
    ].head(20)
)