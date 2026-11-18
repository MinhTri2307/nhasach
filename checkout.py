from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    session,
    current_app,
)

from extensions import db
from forms import CheckoutForm, PAYMENT_LABELS
from models import Order, OrderItem, OrderLog, PENDING
from shop import build_cart

bp = Blueprint("checkout", __name__)


def shipping_fee(subtotal):
    config = current_app.config
    if subtotal >= config["FREE_SHIPPING_FROM"]:
        return 0
    return config["SHIPPING_FEE"]


@bp.route("/checkout", methods=["GET", "POST"])
def checkout():
    lines, subtotal = build_cart()

    if not lines:
        flash("Giỏ hàng trống, hãy chọn sách trước khi đặt hàng.", "warning")
        return redirect(url_for("shop.cart_view"))

    fee = shipping_fee(subtotal)
    form = CheckoutForm()

    if form.validate_on_submit():
        problems = []
        for line in lines:
            book = line["book"]
            if book.stock <= 0:
                problems.append(f"\"{book.title}\" đã hết hàng")
            elif book.stock < line["quantity"]:
                problems.append(
                    f"\"{book.title}\" chỉ còn {book.stock} cuốn "
                    f"(bạn chọn {line['quantity']})"
                )

        if problems:
            flash("Không thể đặt hàng: " + "; ".join(problems) + ".", "danger")
            return redirect(url_for("shop.cart_view"))

        order = Order(
            customer_name=form.name.data,
            phone=form.phone.data,
            email=form.email.data or "",
            address=form.address.data,
            note=form.note.data or "",
            payment_method=PAYMENT_LABELS[form.payment.data],
            shipping_fee=fee,
            status=PENDING,
        )
        db.session.add(order)

        for line in lines:
            book = line["book"]
            order.items.append(
                OrderItem(
                    book_id=book.id,
                    quantity=line["quantity"],
                    unit_price=book.price,
                )
            )
            book.stock -= line["quantity"]

        order.logs.append(OrderLog(status=PENDING))
        db.session.commit()

        session.pop("cart", None)
        return redirect(url_for("checkout.order_success", order_id=order.id))

    return render_template(
        "checkout.html",
        form=form,
        lines=lines,
        subtotal=subtotal,
        fee=fee,
        total=subtotal + fee,
    )


@bp.route("/orders/<int:order_id>")
def order_success(order_id):
    order = db.get_or_404(Order, order_id)
    return render_template("order_success.html", order=order)