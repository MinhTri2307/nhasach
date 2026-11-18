import os

from flask import Flask, render_template, session, flash, redirect, request, url_for

from config import Config
from extensions import db, migrate, csrf


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    import models
    from shop import bp as shop_bp
    from checkout import bp as checkout_bp
    from admin import bp as admin_bp
    from admin_books import bp as admin_books_bp
    from admin_categories import bp as admin_categories_bp
    from admin_orders import bp as admin_orders_bp
    from admin_common import pending_count, status_class

    app.register_blueprint(shop_bp)
    app.register_blueprint(checkout_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(admin_books_bp)
    app.register_blueprint(admin_categories_bp)
    app.register_blueprint(admin_orders_bp)

    app.add_template_global(pending_count, "pending_count")
    app.add_template_filter(status_class, "status_class")

    @app.template_filter("vnd")
    def vnd(value):
        return f"{value:,.0f}".replace(",", ".") + " đ"

    @app.context_processor
    def inject_cart():
        cart = session.get("cart", {})
        return {"cart_count": sum(cart.values())}

    @app.errorhandler(404)
    def not_found(error):
        return render_template("404.html"), 404

    @app.errorhandler(413)
    def too_large(error):
        flash("Tệp tải lên quá lớn (tối đa 2 MB).", "danger")
        return redirect(request.referrer or url_for("shop.book_list"))

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)