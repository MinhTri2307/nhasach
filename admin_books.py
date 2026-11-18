import os
import uuid

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
)
from werkzeug.datastructures import FileStorage

from extensions import db
from forms import BookForm
from models import Book, Category, OrderItem
from shop import safe_next

bp = Blueprint("admin_books", __name__, url_prefix="/admin/books")


def save_cover(upload):
    ext = os.path.splitext(upload.filename)[1].lower()
    name = uuid.uuid4().hex + ext
    upload.save(os.path.join(current_app.config["UPLOAD_FOLDER"], name))
    return name


def remove_cover(name):
    if not name:
        return
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], os.path.basename(name))
    if os.path.isfile(path):
        os.remove(path)


@bp.route("")
@bp.route("/")
def book_list():
    q = request.args.get("q", "").strip()
    category_id = request.args.get("category", type=int)
    stock = request.args.get("stock", "")
    page = request.args.get("page", 1, type=int)

    low = current_app.config["LOW_STOCK"]
    per_page = current_app.config["BOOKS_PER_PAGE"]

    query = Book.query
    if q:
        like = f"%{q}%"
        query = query.filter(db.or_(Book.title.ilike(like), Book.author.ilike(like)))
    if category_id:
        query = query.filter(Book.category_id == category_id)
    if stock == "in":
        query = query.filter(Book.stock > 0)
    elif stock == "low":
        query = query.filter(Book.stock > 0, Book.stock <= low)
    elif stock == "out":
        query = query.filter(Book.stock <= 0)

    pagination = query.order_by(Book.created_at.desc(), Book.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    # Xoá hết sách ở trang cuối thì lùi về trang trước
    if page > 1 and not pagination.items:
        return redirect(
            url_for(
                "admin_books.book_list",
                page=max(pagination.pages, 1),
                q=q or None,
                category=category_id,
                stock=stock or None,
            )
        )

    ids = [b.id for b in pagination.items]
    ordered_ids = set()
    if ids:
        ordered_ids = {
            row[0]
            for row in db.session.query(OrderItem.book_id)
            .filter(OrderItem.book_id.in_(ids))
            .distinct()
        }

    categories = Category.query.order_by(Category.name).all()
    return render_template(
        "admin/books.html",
        pagination=pagination,
        books=pagination.items,
        ordered_ids=ordered_ids,
        categories=categories,
        q=q,
        category_id=category_id,
        stock=stock,
        low=low,
    )


@bp.route("/new", methods=["GET", "POST"])
@bp.route("/<int:book_id>/edit", methods=["GET", "POST"])
def book_form(book_id=None):
    book = db.get_or_404(Book, book_id) if book_id else None

    if not Category.query.first():
        flash("Cần có ít nhất một danh mục trước khi thêm sách.", "warning")
        return redirect(url_for("admin_books.book_list"))

    form = BookForm(obj=book, book_id=book_id)

    if form.validate_on_submit():
        is_new = book is None
        if is_new:
            book = Book()
            db.session.add(book)

        book.title = form.title.data
        book.author = form.author.data
        book.category_id = form.category_id.data
        book.year = form.year.data
        book.price = form.price.data
        book.stock = form.stock.data
        book.publisher = form.publisher.data or ""
        book.description = form.description.data or ""

        old_cover = book.cover
        new_cover = None
        upload = form.cover.data
        if isinstance(upload, FileStorage) and upload.filename:
            new_cover = save_cover(upload)
            book.cover = new_cover

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            remove_cover(new_cover)
            raise

        if new_cover:
            remove_cover(old_cover)

        flash(
            f"Đã thêm sách \"{book.title}\"." if is_new
            else f"Đã cập nhật sách \"{book.title}\".",
            "success",
        )
        return redirect(url_for("admin_books.book_list"))

    return render_template("admin/book_form.html", form=form, book=book)


@bp.route("/<int:book_id>/delete", methods=["POST"])
def book_delete(book_id):
    book = db.get_or_404(Book, book_id)
    back = safe_next(request.form.get("next"), url_for("admin_books.book_list"))

    if OrderItem.query.filter_by(book_id=book.id).first():
        flash(f"Không thể xoá \"{book.title}\": sách đã có trong đơn hàng.", "danger")
        return redirect(back)

    title = book.title
    cover = book.cover
    db.session.delete(book)
    db.session.commit()
    remove_cover(cover)

    flash(f"Đã xoá sách \"{title}\".", "success")
    return redirect(back)