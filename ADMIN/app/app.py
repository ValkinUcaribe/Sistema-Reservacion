from flask import Flask, render_template, request, redirect, url_for, session
from functools import wraps
from models import db
from models.productos import Producto  # Importar modelo y db
from models.tutoriales import Tutorial

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_segura'  # Necesaria para usar sesiones

# Configuración de base de datos SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tienda.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar SQLAlchemy con la app
db.init_app(app)

# Simulación de paquetes (memoria temporal)
paquetes = []

# ---------------------------
# Decorador para proteger rutas
# ---------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# ---------------------------
# Rutas
# ---------------------------

@app.route('/')
def index():
    error = session.pop('login_error', None)
    return render_template('login.html', error=error)

@app.route('/admin/login', methods=['POST'])
def admin_login():
    username = request.form['username']
    password = request.form['password']

    if username == 'Adminval' and password == 'Jetlas1234#':
        session['logged_in'] = True
        return redirect(url_for('admin_panel'))
    else:
        session['login_error'] = 'invalid'
        return redirect(url_for('index'))

@app.route('/admin/panel')
@login_required
def admin_panel():
    return render_template('panel.html')

# ---------------------------
# RUTAS PAQUETES
# ---------------------------
@app.route('/admin/paquetes')
@login_required
def admin_paquetes():
    return render_template('paquetes.html', paquetes=paquetes)

@app.route('/admin/paquetes/agregar', methods=['GET', 'POST'])
@login_required
def agregar_paquete():
    if request.method == 'POST':
        nuevo_paquete = {
            'id': paquetes[-1]['id'] + 1 if paquetes else 1,
            'nombre': request.form['nombre'],
            'descripcion': request.form['descripcion'],
            'precio': float(request.form['precio']),
            'moneda': request.form['moneda'],
            'caducacion': request.form['caducacion'],
            'horas': int(request.form['horas'])
        }
        paquetes.append(nuevo_paquete)
        return redirect(url_for('admin_paquetes'))
    return render_template('agregar_paquete.html')

@app.route('/admin/paquetes/editar/<int:paquete_id>', methods=['GET', 'POST'])
@login_required
def editar_paquete(paquete_id):
    paquete = next((p for p in paquetes if p['id'] == paquete_id), None)
    if not paquete:
        return redirect(url_for('admin_paquetes'))

    if request.method == 'POST':
        paquete['nombre'] = request.form['nombre']
        paquete['descripcion'] = request.form['descripcion']
        paquete['precio'] = float(request.form['precio'])
        paquete['moneda'] = request.form['moneda']
        paquete['caducacion'] = request.form['caducacion']
        paquete['horas'] = int(request.form['horas'])
        return redirect(url_for('admin_paquetes'))

    return render_template('editar_paquete.html', paquete=paquete)

@app.route('/admin/paquetes/eliminar/<int:paquete_id>')
@login_required
def eliminar_paquete(paquete_id):
    global paquetes
    paquetes = [p for p in paquetes if p['id'] != paquete_id]
    return redirect(url_for('admin_paquetes'))

# ---------------------------
# RUTAS TUTORIALES
# ---------------------------
@app.route('/admin/tutoriales')
def admin_tutoriales():
    tutoriales = Tutorial.query.all()
    return render_template('admin_tutoriales.html', tutoriales=tutoriales)

@app.route('/admin/tutoriales/agregar', methods=['GET', 'POST'])
@login_required  # solo si usas login_required para proteger admin
def agregar_tutorial():
    if request.method == 'POST':
        titulo = request.form['titulo']
        video_id = request.form['video_id']

        # Aquí usas tu modelo Tutorial o INSERT directo si es SQL
        nuevo_tutorial = Tutorial(titulo=titulo, video_id=video_id)
        db.session.add(nuevo_tutorial)
        db.session.commit()

        return redirect(url_for('admin_tutoriales'))  # Ajusta si tu endpoint tiene otro nombre

    return render_template('agregar_tutorial.html')

@app.route('/admin/tutoriales/editar/<int:tutorial_id>', methods=['GET', 'POST'])
@login_required
def editar_tutorial(tutorial_id):
    tutorial = Tutorial.query.get_or_404(tutorial_id)

    if request.method == 'POST':
        tutorial.titulo = request.form['titulo']
        tutorial.video_id = request.form['video_id']
        db.session.commit()
        return redirect(url_for('admin_tutoriales'))

    return render_template('editar_tutorial.html', tutorial=tutorial)

@app.route('/admin/tutoriales/eliminar/<int:tutorial_id>')
@login_required
def eliminar_tutorial(tutorial_id):
    tutorial = Tutorial.query.get_or_404(tutorial_id)
    db.session.delete(tutorial)
    db.session.commit()
    return redirect(url_for('admin_tutoriales'))

@app.route('/tutoriales')
def ver_videos():
    tutoriales = Tutorial.query.all()
    return render_template('tutoriales.html', tutoriales=tutoriales)


# ---------------------------
# RUTAS TIENDA
# ---------------------------
@app.route('/admin/tienda', methods=['GET', 'POST'])
@login_required
def admin_tienda():
    if request.method == 'POST':
        nuevo_producto = Producto(
            nombre=request.form['nombre'],
            descripcion=request.form['descripcion'],
            imagen_url=request.form['imagen_url'],
            link_amazon=request.form['link_amazon']
        )
        db.session.add(nuevo_producto)
        db.session.commit()
        return redirect(url_for('admin_tienda'))
    
    productos = Producto.query.all()
    return render_template('admin_tienda.html', productos=productos)

@app.route('/admin/tienda/agregar', methods=['GET', 'POST'])
@login_required
def agregar_producto():
    if request.method == 'POST':
        nuevo_producto = Producto(
            nombre=request.form['nombre'],
            descripcion=request.form['descripcion'],
            imagen_url=request.form['imagen_url'],
            link_amazon=request.form['link_amazon']
        )
        db.session.add(nuevo_producto)
        db.session.commit()
        return redirect(url_for('admin_tienda'))
    
    return render_template('agregar_producto.html')

@app.route('/admin/tienda/editar/<int:producto_id>', methods=['GET', 'POST'])
@login_required
def editar_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)

    if request.method == 'POST':
        producto.nombre = request.form['nombre']
        producto.descripcion = request.form['descripcion']
        producto.imagen_url = request.form['imagen_url']
        producto.link_amazon = request.form['link_amazon']
        db.session.commit()
        return redirect(url_for('admin_tienda'))

    return render_template('editar_producto.html', producto=producto)

@app.route('/admin/tienda/eliminar/<int:producto_id>')
@login_required
def eliminar_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    db.session.delete(producto)
    db.session.commit()
    return redirect(url_for('admin_tienda'))

@app.route('/tienda')
def ver_tienda():
    productos = Producto.query.all()
    return render_template('tienda.html', productos=productos)

# ---------------------------
# LOGOUT
# ---------------------------
@app.route('/admin/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ---------------------------
# CREACIÓN DE BD
# ---------------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
