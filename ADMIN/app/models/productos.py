from models import db  # ✅ Usa la instancia global que creaste

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    imagen_url = db.Column(db.String(255), nullable=False)
    link_amazon = db.Column(db.String(255), nullable=False)

    def _repr_(self):
        return f'<Producto {self.nombre}>'