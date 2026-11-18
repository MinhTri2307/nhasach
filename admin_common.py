from sqlalchemy import func

from extensions import db
from models import Order, PENDING, SHIPPING, DONE, CANCELLED

STATUS_CLASS = {
    PENDING: "st-pending",
    SHIPPING: "st-shipping",
    DONE: "st-done",
    CANCELLED: "st-cancelled",
}


def pending_count():
    return (
        db.session.query(func.count(Order.id))
        .filter(Order.status == PENDING)
        .scalar()
    )


def status_class(status):
    return STATUS_CLASS.get(status, "st-cancelled")