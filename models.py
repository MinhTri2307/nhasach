from datetime import datetime

from extensions import db

PENDING = "Chờ xác nhận"
SHIPPING = "Đang giao"
DONE = "Hoàn tất"
CANCELLED = "Đã huỷ"

STATUSES = [PENDING, SHIPPING, DONE, CANCELLED]

TRANSITIONS = {
    PENDING: [SHIPPING, CANCELLED],
    SHIPPING: [DONE, CANCELLED],
    DONE: [],
    CANCELLED: [],
}


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, default="")

    books = db.relationship("Book", back_populates="category")

    def __repr__(self):
        return f"<Category {self.name}>"


class Book(db.Model):
    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(150), nullable=False)
    publisher = db.Column(db.String(150), default="")
    year = db.Column(db.Integer)
    price = db.Column(db.Integer, nullable=False, default=0)
    stock = db.Column(db.Integer, nullable=False, default=0)
    description = db.Column(db.Text, default="")
    cover = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.now)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)

    category = db.relationship("Category", back_populates="books")
    order_items = db.relationship("OrderItem", back_populates="book")

    def __repr__(self):
        return f"<Book {self.title}>"


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(10), nullable=False)
    email = db.Column(db.String(150), default="")
    address = db.Column(db.String(300), nullable=False)
    note = db.Column(db.String(300), default="")
    payment_method = db.Column(db.String(50), nullable=False)
    shipping_fee = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(30), nullable=False, default=PENDING)
    created_at = db.Column(db.DateTime, default=datetime.now)

    items = db.relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )
    logs = db.relationship(
        "OrderLog",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderLog.created_at",
    )

    @property
    def subtotal(self):
        return sum(i.line_total for i in self.items)

    @property
    def total(self):
        return self.subtotal + self.shipping_fee

    def __repr__(self):
        return f"<Order #{self.id}>"


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Integer, nullable=False)

    order = db.relationship("Order", back_populates="items")
    book = db.relationship("Book", back_populates="order_items")

    @property
    def line_total(self):
        return self.quantity * self.unit_price


class OrderLog(db.Model):
    __tablename__ = "order_logs"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    status = db.Column(db.String(30), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    order = db.relationship("Order", back_populates="logs")