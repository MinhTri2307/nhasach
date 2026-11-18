from flask import Blueprint, render_template, redirect, url_for, flash
from sqlalchemy import func

from extensions import db
from forms import CategoryForm
from models import Book, Category

bp = Blueprint("admin_categories", __name__, url_prefix="/admin/categories")


def categories_with_counts():
    # Một truy vấn group_by; outer join để danh mục chưa có sách vẫn hiện (0)
    return (
        db.session.query(Category, func.count(Book.id))
        .outerjoin(Book, Book.category_id == Category.id)
        .group_by(Category.id)
        .order_by(Category.id)
        .all()
    )


@bp.route("", methods=["GET", "POST"])
@bp.route("/", methods=["GET", "POST"])
@bp.route("/<int:category_id>/edit", methods=["GET", "POST"])
def category_list(category_id=None):
    category = db.get_or_404(Category, category_id) if category_id else None
    form = CategoryForm(obj=category, category_id=category_id)

    if form.validate_on_submit():
        if category is None:
            category = Category()
            db.session.add(category)
            message = f"Đã thêm danh mục \"{form.name.data}\"."
        else:
            message = f"Đã cập nhật danh mục \"{form.name.data}\"."

        category.name = form.name.data
        category.description = form.description.data or ""
        db.session.commit()

        flash(message, "success")
        return redirect(url_for("admin_categories.category_list"))

    rows = categories_with_counts()
    return render_template(
        "admin/categories.html",
        rows=rows,
        form=form,
        editing=category,
    )


@bp.route("/<int:category_id>/delete", methods=["POST"])
def category_delete(category_id):
    category = db.get_or_404(Category, category_id)

    book_count = (
        db.session.query(func.count(Book.id))
        .filter(Book.category_id == category.id)
        .scalar()
    )
    if book_count:
        flash(
            f"Không thể xoá \"{category.name}\": còn {book_count} sách.",
            "danger",
        )
        return redirect(url_for("admin_categories.category_list"))

    name = category.name
    db.session.delete(category)
    db.session.commit()

    flash(f"Đã xoá danh mục \"{name}\".", "success")
    return redirect(url_for("admin_categories.category_list"))