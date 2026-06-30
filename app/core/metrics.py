from prometheus_client import Counter

LOGIN_ATTEMPTS = Counter("login_attempts_total", "Total number of login attempts", ["status"])
USERS_CREATED = Counter("users_created_total", "Total number of registered users")

ORDERS_CREATED = Counter("orders_created_total", "Total number of created orders")
ORDERS_COMPLETED = Counter("orders_completed_total", "Total number of successfully completed orders")
ORDERS_CANCELED = Counter("orders_canceled_total", "Total number of canceled orders")

PRODUCTS_CREATED = Counter("products_created_total", "Total number of created products")
PRODUCT_SEARCHES = Counter("product_searches_total", "Total number of product search requests")

CHAT_ROOMS_CREATED = Counter("chat_rooms_created_total", "Total number of created chat rooms")
CHAT_MESSAGES_SENT = Counter("chat_messages_sent_total", "Total number of sent chat messages")

MEDIA_PROCESSED = Counter("media_processed_total", "Total number of processed media files", ["entity_type"])
