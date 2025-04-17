from models import db  # ✅ Usa la instancia global que creaste

class Tutorial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    video_id = db.Column(db.String(20), nullable=False)