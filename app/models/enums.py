from enum import Enum

class OrderStatus(str, Enum):
    created = "created"
    paid = "paid"
    shipped = "shipped"
    completed = "completed"
    cancelled = "cancelled"

class EscrowStatus(str, Enum):
    initiated = "initiated"
    funded = "funded"
    released = "released"
    refunded = "refunded"
    cancelled = "cancelled"

class MessageType(str, Enum):
    text = "text"
    image = "image"
    system = "system"
