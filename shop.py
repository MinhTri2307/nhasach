from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
)

from extensions import db
from models import Book, Category

bp = Blueprint("shop", __name__)


def get_cart():
    return session.get("cart", {})


def cart_quantity(book_id):
    return get_cart().get(str(book_id), 0)


def safe_next(target, fallback):
    if target and target.startswith("/") and not target.startswith(("//", "/\\")):
        return target
    return fallback


def build_cart():
    cart = get_cart()
    ids = [int(key) for key in cart]
    books = {}
    if ids:
        books = {b.id: b for b in Book.query.filter(Book.id.in_(ids)).all()}

    lines = []
    total = 0
    for key, quantity in cart.items():
        book = books.get(int(key))
        if book is None:
            continue
        line_total = book.price * quantity
        total += line_total
        lines.append({"book": book, "quantity": quantity, "line_total": line_total})

    lines.sort(key=lambda line: line["book"].id)
    return lines, total


@bp.route("/")
def home():
    return redirect(url_for("shop.book_list"))


@bp.route("/books")
def book_list():
    q = request.args.get("q", "").strip()
    category_id = request.args.get("category", type=int)

    query = Book.query
    if q:
        like = f"%{q}%"
        query = query.filter(db.or_(Book.title.ilike(like), Book.author.ilike(like)))
    if category_id:
        query = query.filter(Book.category_id == category_id)

    books = query.order_by(Book.id).all()
    categories = Category.query.order_by(Category.name).all()
    return render_template(
        "books/list.html",
        books=books,
        categories=categories,
        q=q,
        category_id=category_id,
    )


@bp.route("/books/<int:book_id>")
def book_detail(book_id):
    book = db.get_or_404(Book, book_id)
    in_cart = cart_quantity(book.id)
    max_qty = max(book.stock - in_cart, 0)
    return render_template(
        "books/detail.html", book=book, in_cart=in_cart, max_qty=max_qty
    )


@bp.route("/cart/add/<int:book_id>", methods=["POST"])
def cart_add(book_id):
    book = db.get_or_404(Book, book_id)
    back = safe_next(
        request.form.get("next"), url_for("shop.book_detail", book_id=book.id)
    )

    try:
        quantity = int(request.form.get("quantity", "1"))
    except ValueError:
        flash("Số lượng không hợp lệ.", "danger")
        return redirect(back)

    in_cart = cart_quantity(book.id)
    available = book.stock - in_cart

    if book.stock <= 0:
        flash(f"Sách \"{book.title}\" đã hết hàng.", "danger")
        return redirect(back)

    if quantity < 1:
        flash("Số lượng phải từ 1 trở lên.", "danger")
        return redirect(back)

    if quantity > available:
        flash(
            f"Chỉ có thể thêm tối đa {max(available, 0)} cuốn "
            f"(tồn kho {book.stock}, đã có {in_cart} trong giỏ).",
            "danger",
        )
        return redirect(back)

    cart = dict(get_cart())
    cart[str(book.id)] = in_cart + quantity
    session["cart"] = cart

    flash(f"Đã thêm {quantity} × {book.title} vào giỏ hàng.", "success")
    return redirect(back)


@bp.route("/cart")
def cart_view():
    lines, total = build_cart()

    valid = {str(line["book"].id): line["quantity"] for line in lines}
    if valid != get_cart():
        session["cart"] = valid

    return render_template("cart.html", lines=lines, total=total)


@bp.route("/cart/increase/<int:book_id>", methods=["POST"])
def cart_increase(book_id):
    book = db.session.get(Book, book_id)
    cart = dict(get_cart())
    key = str(book_id)

    if book is None or key not in cart:
        flash("Sách không có trong giỏ hàng.", "danger")
    elif cart[key] >= book.stock:
        flash(f"Chỉ còn {book.stock} cuốn \"{book.title}\" trong kho.", "danger")
    else:
        cart[key] += 1
        session["cart"] = cart

    return redirect(url_for("shop.cart_view"))


@bp.route("/cart/decrease/<int:book_id>", methods=["POST"])
def cart_decrease(book_id):
    cart = dict(get_cart())
    key = str(book_id)

    if key in cart:
        cart[key] -= 1
        if cart[key] <= 0:
            del cart[key]
        session["cart"] = cart
    else:
        flash("Sách không có trong giỏ hàng.", "danger")

    return redirect(url_for("shop.cart_view"))


@bp.route("/cart/remove/<int:book_id>", methods=["POST"])
def cart_remove(book_id):
    cart = dict(get_cart())
    key = str(book_id)

    if key in cart:
        del cart[key]
        session["cart"] = cart
        flash("Đã xoá sách khỏi giỏ hàng.", "success")
    else:
        flash("Sách không có trong giỏ hàng.", "danger")

    return redirect(url_for("shop.cart_view"))


@bp.route("/cart/clear", methods=["POST"])
def cart_clear():
    session.pop("cart", None)
    flash("Đã xoá toàn bộ giỏ hàng.", "success")
    return redirect(url_for("shop.cart_view"))