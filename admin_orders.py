from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
)
from sqlalchemy import func
from sqlalchemy.orm import selectinload

from admin import items_subtotal
from extensions import db
from models import (
    Order,
    OrderLog,
    STATUSES,
    TRANSITIONS,
    PENDING,
    SHIPPING,
    DONE,
    CANCELLED,
)

bp = Blueprint("admin_orders", __name__, url_prefix="/admin/orders")

FLOW = [PENDING, SHIPPING, DONE]


def build_conditions(q, status):
    conds = []
    if status:
        conds.append(Order.status == status)
    if q:
        like = f"%{q}%"
        parts = [Order.customer_name.ilike(like), Order.phone.ilike(like)]
        code = q.lstrip("#")
        if code.isdigit():
            parts.append(Order.id == int(code))
        conds.append(db.or_(*parts))
    return conds


@bp.route("")
@bp.route("/")
def order_list():
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "")
    if status not in STATUSES:
        status = ""
    page = request.args.get("page", 1, type=int)
    per_page = current_app.config["ORDERS_PER_PAGE"]

    # Số đơn theo từng trạng thái: một truy vấn group_by
    counts = dict(
        db.session.query(Order.status, func.count(Order.id))
        .group_by(Order.status)
        .all()
    )
    total_all = sum(counts.values())

    conds = build_conditions(q, status)

    pagination = (
        Order.query.filter(*conds)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc(), Order.id.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    if page > 1 and not pagination.items:
        return redirect(
            url_for(
                "admin_orders.order_list",
                page=max(pagination.pages, 1),
                q=q or None,
                status=status or None,
            )
        )

    # Dòng cuối: số đơn và tổng giá trị của bộ lọc hiện tại
    sub = items_subtotal()
    summary_count, summary_total = (
        db.session.query(
            func.count(Order.id),
            func.coalesce(
                func.sum(func.coalesce(sub.c.subtotal, 0) + Order.shipping_fee), 0
            ),
        )
        .select_from(Order)
        .outerjoin(sub, sub.c.order_id == Order.id)
        .filter(*conds)
        .one()
    )

    return render_template(
        "admin/orders.html",
        pagination=pagination,
        orders=pagination.items,
        statuses=STATUSES,
        counts=counts,
        total_all=total_all,
        q=q,
        status=status,
        summary_count=summary_count,
        summary_total=int(summary_total),
    )


@bp.route("/<int:order_id>")
def order_detail(order_id):
    order = db.get_or_404(Order, order_id)
    allowed = TRANSITIONS.get(order.status, [])

    upcoming = []
    if order.status in FLOW:
        upcoming = FLOW[FLOW.index(order.status) + 1:]

    return render_template(
        "admin/order_detail.html",
        order=order,
        next_statuses=[s for s in allowed if s != CANCELLED],
        can_cancel=CANCELLED in allowed,
        upcoming=upcoming,
    )


def apply_status(order, new_status):
    """Đổi trạng thái nếu hợp lệ. Trả về True/False, tự flash lỗi."""
    if new_status not in TRANSITIONS.get(order.status, []):
        flash(
            f"Không thể chuyển đơn #{order.id} từ \"{order.status}\" "
            f"sang \"{new_status}\".",
            "danger",
        )
        return False

    if new_status == CANCELLED:
        for item in order.items:
            item.book.stock += item.quantity

    order.status = new_status
    order.logs.append(OrderLog(status=new_status))
    db.session.commit()
    return True


@bp.route("/<int:order_id>/status", methods=["POST"])
def order_status(order_id):
    order = db.get_or_404(Order, order_id)
    new_status = request.form.get("status", "")

    if apply_status(order, new_status):
        flash(f"Đã chuyển đơn #{order.id} sang \"{new_status}\".", "success")
    return redirect(url_for("admin_orders.order_detail", order_id=order.id))


@bp.route("/<int:order_id>/cancel", methods=["POST"])
def order_cancel(order_id):
    order = db.get_or_404(Order, order_id)

    if apply_status(order, CANCELLED):
        flash(f"Đã huỷ đơn #{order.id}, tồn kho đã được hoàn lại.", "success")
    return redirect(url_for("admin_orders.order_detail", order_id=order.id))