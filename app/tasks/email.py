from app.core.celery import celery_app


@celery_app.task
def send_order_confirmation(buyer_email: str, order_id: str, total_price: float) -> None:
    message = (
        f"EMAIL: Confirmation for Order {order_id}\n"
        f"Dear Customer ({buyer_email}),\n\n"
        f"Your order has been placed successfully!\n"
        f"Total Price: ${total_price:.2f}\n\n"
        "Thank you for shopping with us!"
    )
    print(message)
