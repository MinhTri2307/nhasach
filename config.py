import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = "doi-khoa-bi-mat-nay"
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "nhasach.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024
    SHIPPING_FEE = 20000
    FREE_SHIPPING_FROM = 200000
    LOW_STOCK = 5
    BOOKS_PER_PAGE = 5
    ORDERS_PER_PAGE = 10