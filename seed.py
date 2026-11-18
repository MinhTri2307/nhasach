from app import app
from extensions import db
from models import Category, Book


def run():
    with app.app_context():
        if Category.query.first():
            print("Dữ liệu mẫu đã có, bỏ qua")
            return

        cats = {
            name: Category(name=name, description=desc)
            for name, desc in [
                ("Lập trình", "Sách về ngôn ngữ và kỹ thuật lập trình"),
                ("Cơ sở dữ liệu", "Sách về CSDL và SQL"),
                ("Công cụ", "Git, Docker và các công cụ phát triển"),
                ("Mạng", "Mạng máy tính"),
                ("Kỹ năng lập trình", "Clean code, kiến trúc phần mềm"),
                ("Thiết kế", "Thiết kế giao diện và trải nghiệm"),
            ]
        }
        db.session.add_all(cats.values())
        db.session.flush()

        books = [
            ("Lập trình Python cơ bản", "Nguyễn Văn A", "NXB Đại học Huế", 2024, 95000, 30, "Lập trình"),
            ("Giáo trình Flask", "Miguel Grinberg", "NXB Giáo dục", 2023, 120000, 20, "Lập trình"),
            ("Cơ sở dữ liệu", "Trần Văn B", "NXB Đại học Huế", 2022, 85000, 0, "Cơ sở dữ liệu"),
            ("Pro Git", "Scott Chacon", "NXB Thông tin", 2021, 150000, 15, "Công cụ"),
            ("Mạng máy tính", "Lê Văn C", "NXB Khoa học", 2020, 110000, 12, "Mạng"),
            ("Clean Code", "Robert C. Martin", "NXB Lao động", 2008, 180000, 5, "Kỹ năng lập trình"),
        ]
        for title, author, pub, year, price, stock, cat in books:
            db.session.add(
                Book(
                    title=title,
                    author=author,
                    publisher=pub,
                    year=year,
                    price=price,
                    stock=stock,
                    description=f"Mô tả cho cuốn {title}.",
                    category_id=cats[cat].id,
                )
            )

        db.session.commit()
        print("Đã tạo dữ liệu mẫu")


if __name__ == "__main__":
    run()