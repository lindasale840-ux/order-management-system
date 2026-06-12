from repositories.order_repository import OrderRepository

df = OrderRepository.get_all_orders()

print(df["sale_owner"].dropna().unique())