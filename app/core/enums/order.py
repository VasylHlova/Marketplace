import enum


class OrderStatus(enum.StrEnum):
    ACTIVE = "active"
    CANCELED = "canceled"
    COMPLETED = "completed"
