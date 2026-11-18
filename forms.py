import os
from datetime import datetime

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField,
    TextAreaField,
    RadioField,
    IntegerField,
    SelectField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    InputRequired,
    Length,
    NumberRange,
    Optional,
    Regexp,
    ValidationError,
)

from models import Book, Category

PAYMENT_LABELS = {
    "cod": "Tiền mặt khi nhận hàng",
    "bank": "Chuyển khoản",
}

MAX_COVER_BYTES = 2 * 1024 * 1024


def strip(value):
    return value.strip() if isinstance(value, str) else value


class CheckoutForm(FlaskForm):
    name = StringField(
        "Họ tên",
        filters=[strip],
        validators=[
            DataRequired(message="Vui lòng nhập họ tên."),
            Length(max=150, message="Họ tên tối đa 150 ký tự."),
        ],
    )
    phone = StringField(
        "Số điện thoại",
        filters=[strip],
        validators=[
            DataRequired(message="Vui lòng nhập số điện thoại."),
            Regexp(r"^0\d{9}$", message="Số điện thoại gồm 10 chữ số, bắt đầu bằng 0."),
        ],
    )
    email = StringField(
        "Email",
        filters=[strip],
        validators=[
            Optional(),
            Email(message="Email không đúng định dạng."),
            Length(max=150, message="Email tối đa 150 ký tự."),
        ],
    )
    address = TextAreaField(
        "Địa chỉ giao hàng",
        filters=[strip],
        validators=[
            DataRequired(message="Vui lòng nhập địa chỉ giao hàng."),
            Length(max=300, message="Địa chỉ tối đa 300 ký tự."),
        ],
    )
    note = TextAreaField(
        "Ghi chú",
        filters=[strip],
        validators=[Optional(), Length(max=300, message="Ghi chú tối đa 300 ký tự.")],
    )
    payment = RadioField(
        "Thanh toán",
        choices=list(PAYMENT_LABELS.items()),
        default="cod",
        validators=[DataRequired(message="Vui lòng chọn hình thức thanh toán.")],
    )


class VNIntegerField(IntegerField):
    """IntegerField báo lỗi bằng tiếng Việt."""

    def process_formdata(self, valuelist):
        if not valuelist:
            return
        try:
            self.data = int(valuelist[0])
        except ValueError:
            self.data = None
            raise ValueError("Vui lòng nhập số nguyên.")


class BookForm(FlaskForm):
    title = StringField(
        "Tên sách",
        filters=[strip],
        validators=[
            DataRequired(message="Vui lòng nhập tên sách."),
            Length(max=200, message="Tên sách tối đa 200 ký tự."),
        ],
    )
    author = StringField(
        "Tác giả",
        filters=[strip],
        validators=[
            DataRequired(message="Vui lòng nhập tác giả."),
            Length(max=150, message="Tác giả tối đa 150 ký tự."),
        ],
    )
    category_id = SelectField(
        "Danh mục",
        coerce=int,
        validators=[InputRequired(message="Vui lòng chọn danh mục.")],
    )
    year = VNIntegerField("Năm xuất bản", validators=[Optional()])
    price = VNIntegerField(
        "Giá (đồng)",
        validators=[
            InputRequired(message="Vui lòng nhập giá."),
            NumberRange(min=1000, message="Giá tối thiểu 1.000 đồng."),
        ],
    )
    stock = VNIntegerField(
        "Tồn kho",
        validators=[
            InputRequired(message="Vui lòng nhập tồn kho."),
            NumberRange(min=0, message="Tồn kho không âm."),
        ],
    )
    publisher = StringField(
        "Nhà xuất bản",
        filters=[strip],
        validators=[Optional(), Length(max=150, message="NXB tối đa 150 ký tự.")],
    )
    description = TextAreaField("Mô tả", filters=[strip], validators=[Optional()])
    cover = FileField(
        "Ảnh bìa",
        validators=[
            Optional(),
            FileAllowed(["jpg", "jpeg", "png", "webp"], "Chỉ nhận ảnh JPG, PNG hoặc WEBP."),
        ],
    )

    def __init__(self, *args, book_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.book_id = book_id
        self.category_id.choices = [
            (c.id, c.name) for c in Category.query.order_by(Category.name).all()
        ]

    def validate_title(self, field):
        wanted = field.data.casefold()
        for book_id, title in Book.query.with_entities(Book.id, Book.title).all():
            if book_id != self.book_id and title.casefold() == wanted:
                raise ValidationError("Tên sách đã tồn tại.")

    def validate_year(self, field):
        if field.data is None:
            return
        now = datetime.now().year
        if not 1900 <= field.data <= now:
            raise ValidationError(f"Năm xuất bản từ 1900 đến {now}.")

    def validate_cover(self, field):
        upload = field.data
        if not upload or not getattr(upload, "filename", ""):
            return
        upload.stream.seek(0, os.SEEK_END)
        size = upload.stream.tell()
        upload.stream.seek(0)
        if size > MAX_COVER_BYTES:
            raise ValidationError("Ảnh bìa tối đa 2 MB.")


class CategoryForm(FlaskForm):
    name = StringField(
        "Tên",
        filters=[strip],
        validators=[
            DataRequired(message="Vui lòng nhập tên danh mục."),
            Length(max=100, message="Tên danh mục tối đa 100 ký tự."),
        ],
    )
    description = TextAreaField(
        "Mô tả",
        filters=[strip],
        validators=[Optional(), Length(max=500, message="Mô tả tối đa 500 ký tự.")],
    )

    def __init__(self, *args, category_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.category_id = category_id

    def validate_name(self, field):
        wanted = field.data.casefold()
        for cat_id, name in Category.query.with_entities(Category.id, Category.name).all():
            if cat_id != self.category_id and name.casefold() == wanted:
                raise ValidationError("Danh mục đã tồn tại.")