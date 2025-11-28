from flask import Flask, jsonify,request, Response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.engine import URL
import matplotlib
matplotlib.use('Agg')   # 👈 backend no interactivo
import matplotlib.pyplot as plt
import io
import datetime
from sqlalchemy import extract, func
from flask_cors import CORS

# Configuración de la app Flask
app = Flask(__name__)
CORS(app)  # habilita CORS para toda la app
'''
CORS(app, resources={
        r"/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
        }
    })
'''
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "postgresql+psycopg2://jamaroguevara:Cb8npR5KCFVcUjRekiXd4eNVsGofnOzr@dpg-d432g0buibrs73ajps40-a.oregon-postgres.render.com/jamarog_db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Modelos
class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String, nullable=False)
    price = db.Column(db.Numeric(12, 2), nullable=False)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String)

class Branch(db.Model):
    __tablename__ = "branches"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)

class Sale(db.Model):
    __tablename__ = "sales"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date)
    unit_price = db.Column(db.Numeric(12, 2))
    quantity = db.Column(db.Integer)
    total = db.Column(db.Numeric(14, 2))
    producto_id = db.Column(db.Integer, db.ForeignKey("products.id"))
    branch_id = db.Column(db.Integer, db.ForeignKey("branches.id"))

# Endpoint para obtener todos los productos
@app.route("/GetAllProd", methods=["GET"])
def GetAllProd():
    products = Product.query.all()
    result = []
    for p in products:
        result.append({
            "id": p.id,
            "sku": p.sku,
            "price": float(p.price),
            "name": p.name,
            "description": p.description
        })
    return jsonify(result)

@app.route("/sales/branches/line-chart", methods=["GET"])
def sales_line_chart():
    # Obtener el año del parámetro o usar el actual
    year = request.args.get("year", default=datetime.datetime.now().year, type=int)

    # Consultar ventas del año por mes y sucursal
    sales_data = (
        db.session.query(
            extract("month", Sale.date).label("month"),
            Branch.name.label("branch"),
            func.sum(Sale.total).label("monthly_total")
        )
        .join(Branch, Sale.branch_id == Branch.id)
        .filter(extract("year", Sale.date) == year)
        .group_by("month", "branch")
        .order_by("month")
        .all()
    )

    if not sales_data:
        return jsonify({"error": f"No hay ventas registradas en el año {year}"}), 404

    # Organizar datos por sucursal
    branch_sales = {}
    for month, branch, total in sales_data:
        month = int(month)
        if branch not in branch_sales:
            branch_sales[branch] = [0] * 12
        branch_sales[branch][month - 1] = float(total)

    # Crear gráfica
    plt.figure(figsize=(10, 6))
    for branch, monthly_totals in branch_sales.items():
        plt.plot(range(1, 13), monthly_totals, label=branch)

    plt.title(f"Ventas mensuales por sucursal - {year}")
    plt.xlabel("Mes")
    plt.ylabel("Total de ventas ($)")
    plt.xticks(range(1, 13))
    plt.legend()
    plt.grid(True)

    # Convertir a imagen PNG
    img = io.BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    plt.close()

    return Response(img.getvalue(), mimetype="image/png")


# Ejecutar la app
if __name__ == "__main__":
    app.run(debug=True)