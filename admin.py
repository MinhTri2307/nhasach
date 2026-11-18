from datetime import date, datetime, timedelta

from flask import Blueprint, render_template, current_app
from sqlalchemy import func

from extensions import db
from models import Book, Order, OrderItem, DONE, PENDING

bp = Blueprint("admin", __name__, url_prefix="/admin")


def month_range(today):
    start = datetime(today.year, today.month, 1)
    if today.month == 12:
        end = datetime(today.year + 1, 1, 1)
    else:
        end = datetime(today.year, today.month + 1, 1)
    return start, end


def items_subtotal():
    return (
        db.session.query(
            OrderItem.order_id.label("order_id"),
            func.sum(OrderItem.quantity * OrderItem.unit_price).label("subtotal"),
        )
        .group_by(OrderItem.order_id)
        .subquery()
    )


def revenue_between(start, end):
    sub = items_subtotal()
    return (
        db.session.query(
            func.coalesce(func.sum(sub.c.subtotal + Order.shipping_fee), 0)
        )
        .select_from(Order)
        .join(sub, sub.c.order_id == Order.id)
        .filter(
            Order.status == DONE,
            Order.created_at >= start,
            Order.created_at < end,
        )
        .scalar()
    )


def daily_revenue(days=7):
    today = date.today()
    start_day = today - timedelta(days=days - 1)
    start = datetime.combine(start_day, datetime.min.time())
    end = datetime.combine(today + timedelta(days=1), datetime.min.time())

    sub = items_subtotal()
    day = func.date(Order.created_at)
    rows = (
        db.session.query(day, func.sum(sub.c.subtotal + Order.shipping_fee))
        .select_from(Order)
        .join(sub, sub.c.order_id == Order.id)
        .filter(
            Order.status == DONE,
            Order.created_at >= start,
            Order.created_at < end,
        )
        .group_by(day)
        .all()
    )
    by_day = {str(d): int(total) for d, total in rows}

    result = []
    for i in range(days):
        d = start_day + timedelta(days=i)
        result.append(
            {"label": d.strftime("%d/%m"), "value": by_day.get(d.isoformat(), 0)}
        )

    peak = max(item["value"] for item in result)
    for item in result:
        item["percent"] = round(item["value"] * 100 / peak) if peak else 0
    return result


@bp.route("")
@bp.route("/")
def dashboard():
    low = current_app.config["LOW_STOCK"]
    today = date.today()
    month_start, month_end = month_range(today)

    book_count = db.session.query(func.count(Book.id)).scalar()
    pending = (
        db.session.query(func.count(Order.id))
        .filter(Order.status == PENDING)
        .scalar()
    )
    revenue = revenue_between(month_start, month_end)
    low_count = (
        db.session.query(func.count(Book.id)).filter(Book.stock <= low).scalar()
    )

    latest_orders = (
        Order.query.order_by(Order.created_at.desc(), Order.id.desc()).limit(5).all()
    )
    low_books = (
        Book.query.filter(Book.stock <= low)
        .order_by(Book.stock, Book.id)
        .limit(10)
        .all()
    )

    return render_template(
        "admin/dashboard.html",
        book_count=book_count,
        pending=pending,
        revenue=revenue,
        low_count=low_count,
        month=today.month,
        low=low,
        latest_orders=latest_orders,
        low_books=low_books,
        chart=daily_revenue(),
    )