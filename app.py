# Librerias a usar
from flask import Flask, request, render_template, redirect, url_for, flash, session, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib
import mysql.connector
from email.message import EmailMessage
from email.mime.image import MIMEImage
import smtplib
import os
import random
import string
from google_auth_oauthlib.flow import Flow
from datetime import datetime, timedelta, date # Importamos datetime
import requests
import stripe
import time
import pytz
from PIL import Image
import io
import base64
from dotenv import load_dotenv

load_dotenv()

# Función para generar un PIN aleatorio de 6 dígitos
def generar_pin():
    return ''.join(random.choices(string.digits, k=6))

# envio de pin con imagen lista falta el de bienvenida y el de envio de token
def cargar_y_modificar_html(ruta_html, pin):
    """
    Carga un archivo HTML y reemplaza las variables dinámicas con enlaces de imágenes en Google Drive.

    :param ruta_html: Ruta del archivo HTML a cargar.
    :param pin: Código PIN generado.
    :return: HTML modificado con los datos dinámicos y enlaces de imágenes.
    """
    try:
        # Leer el contenido del archivo HTML
        with open(ruta_html, "r", encoding="utf-8") as archivo:
            contenido_html = archivo.read()

        # Diccionario de reemplazos en el HTML
        reemplazos = {
            "[Nombre]": "Usuario",
            "[Código]": pin,
            "[Tiempo de validez]": "10",
            "[Correo de soporte]": "soporte@valkin.com",
            "[Teléfono de contacto]": "+52 123 456 7890",
            "[URL_POLÍTICAS]": "https://valkin.com/politicas",
            "[URL_SOPORTE]": "https://valkin.com/soporte",
        }

        # Aplicar los reemplazos en el contenido del HTML
        for clave, valor in reemplazos.items():
            contenido_html = contenido_html.replace(clave, valor)

        return contenido_html

    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo HTML en {ruta_html}.")
        return None

    except Exception as e:
        print(f"❌ Error al procesar el HTML: {e}")
        return None
    

def cargar_y_modificar_html_3(ruta_html, token, horario):
    """
    Carga un archivo HTML y reemplaza algunas variables dinámicas.

    :param ruta_html: Ruta del archivo HTML a cargar.
    :param token: Token de acceso generado.
    :param horario: Horario de la reserva.
    :return: HTML modificado con los datos dinámicos.
    """
    try:
        # Leer el contenido del archivo HTML
        with open(ruta_html, "r", encoding="utf-8") as archivo:
            contenido_html = archivo.read()

        # Diccionario de reemplazos en el HTML
        reemplazos = {
            "[Nombre]": "Usuario",
            "[Token]": token,
            "[Horario]": horario,
            "[Correo de soporte]": "soporte@valkin.com",
            "[Teléfono de contacto]": "+52 123 456 7890",
            "[URL_POLÍTICAS]": "https://valkin.com/politicas",
            "[URL_SOPORTE]": "https://valkin.com/soporte",
        }

        # Aplicar los reemplazos en el contenido del HTML
        for clave, valor in reemplazos.items():
            contenido_html = contenido_html.replace(clave, valor)

        return contenido_html

    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo HTML en {ruta_html}.")
        return None

    except Exception as e:
        print(f"❌ Error al procesar el HTML: {e}")
        return None

def enviar_correo(remitente, contraseña, destino, asunto, html_modificado):
    """
    Envía un correo electrónico con contenido HTML sin adjuntar imágenes.

    :param remitente: Dirección de correo del remitente.
    :param contraseña: Contraseña de la cuenta de correo.
    :param destino: Dirección de correo del destinatario.
    :param asunto: Asunto del correo.
    :param html_modificado: Contenido HTML con los datos personalizados y enlaces de imágenes.
    """
    try:
        # Crear el mensaje de correo
        email = EmailMessage()
        email["From"] = remitente
        email["To"] = destino
        email["Subject"] = asunto

        # Cabeceras anti-spam opcionales
        email["Reply-To"] = remitente
        email["X-Mailer"] = "Python"
        email["X-Priority"] = "3"
        email.set_content("Este correo contiene HTML. Si no lo ves, revisa tu configuración.", subtype='plain')
        email.add_alternative(html_modificado, subtype='html')  # Cuerpo del correo en HTML

        # Configurar SMTP y enviar el correo
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(remitente, contraseña)
            smtp.send_message(email)

        print(f"📩 Correo enviado exitosamente a {destino}.")
    
    except Exception as e:
        print(f"❌ Error al enviar el correo: {e}")

def obtener_ubicacion_y_hora():
    # Realizar la solicitud a la API de ipinfo.io
    response = requests.get('https://ipinfo.io')

    # Parsear la respuesta JSON
    location = response.json()

    # Obtener la ubicación (país, ciudad, región) y concatenarla
    location_full = f"{location.get('city', 'Desconocido')}, {location.get('region', 'Desconocido')}, {location.get('country', 'Desconocido')}"

    # Obtener la zona horaria
    timezone = location.get("timezone", "UTC")  # Por defecto, UTC si no se encuentra zona horaria

    # Convertir la hora actual a la zona horaria local
    local_tz = pytz.timezone(timezone)
    local_time = datetime.now(local_tz)

    # Obtener fecha y hora local como variables
    fecha_local = local_time.strftime("%Y-%m-%d")  # Formato: YYYY-MM-DD
    hora_local = local_time.strftime("%H:%M:%S")  # Formato: HH:MM:SS

    # Retornar todas las variables en un diccionario
    return {
        "ubicacion_completa": location_full,
        "fecha_local": fecha_local,
        "hora_local": hora_local
    }

# Crear un archivo con variables y tomarlas de aqui
# Configuración de la base de datos
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 3306)),  # Convierte a entero con valor por defecto
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}

# Variable para el uso de autenticacion de google
state_global = None

id_usuario_global = None
correo_usuario_global = None
nombre_usuario_global = None
nombre_usuario = None
correo_usuario = None
pin = None
pin_timestamp = None  # Tiempo en que se generó el PIN
PIN_EXPIRATION_SECONDS = 300  # Por ejemplo, 5 minutos
id_paquete_seleccionado = 0 

# banderas
usuario_google = False
usuario_normal = False
primera_compra = False

# Inicializar la aplicación Flask
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# Para la pasarela de pago
app.config['STRIPE_PUBLIC_KEY'] = os.getenv('STRIPE_PUBLIC_KEY')
app.config['STRIPE_SECRET_KEY'] = os.getenv('STRIPE_SECRET_KEY')
stripe.api_key = app.config['STRIPE_SECRET_KEY']

# Ruta donde está la plantilla HTML
RUTA_CARPETA = "templates"  
ARCHIVO_HTML = "Codigo_verificacion.html"

# Configuración del remitente y contraseña de donde se va enviar los correos
REMITENTE = os.getenv("EMAIL_REMITENTE")
CONTRASEÑA = os.getenv("EMAIL_CONTRASEÑA")

# Crear conexión global a la base de datos
def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except mysql.connector.Error as e:
        print("Error al conectar a la base de datos:", e)
        return None

# Ruta de Login
@app.route('/', methods=['GET', 'POST'])
def login():
    global id_usuario_global, usuario_normal, nombre_usuario,  usuario_google

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True, buffered=True)
                query = "SELECT * FROM Usuarios WHERE correo = %s LIMIT 1"
                cursor.execute(query, (email,))
                user = cursor.fetchone()

                if user and user['contrasena'] and check_password_hash(user['contrasena'], password):
                    session['user_id'] = user['id_usuario']  # Guarda solo el ID en la sesión
                    session['user_nombre'] = user['nombre']  # Guarda el nombre del usuario en la sesión
                    id_usuario_global = user['id_usuario']
                    nombre_usuario = user['nombre']
                    

                    usuario_normal = True
                    usuario_google = False
                    print(nombre_usuario)
                    print(usuario_normal)
                    print(usuario_google)

                    # Redirige al usuario a la ruta 'home' después de un login exitoso
                    return redirect(url_for('home'))
                else:
                    flash("Correo o contraseña incorrectos", "error")
                    return redirect(url_for('login'))
            except mysql.connector.Error as err:
                print(f"Error en la consulta: {err}")
                flash("Error interno del servidor", "error")
                return redirect(url_for('login'))
            finally:
                cursor.close()
                connection.close()
        else:
            flash("Error al conectar a la base de datos", "error")
            return redirect(url_for('login'))

    return render_template('Login.html')
# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Función de registro de usuario a la página
@app.route('/registro', methods=['GET', 'POST'])
def register():
    global nombre_usuario, correo_usuario

    if request.method == 'POST':
        # Capturar datos del formulario
        email = request.form.get('email')
        nombre = request.form.get('nombre')
        terms_conditions = request.form.get('terms_conditions')
        privacy_policy = request.form.get('privacy_policy')

        # Validar que no haya campos vacíos
        if not email or not nombre:
            flash("Todos los campos son obligatorios.", "error")
            return redirect(url_for('register'))

        # Verificar que el usuario haya aceptado los términos y el aviso de privacidad
        if not terms_conditions or not privacy_policy:
            flash("Debes aceptar los términos y condiciones y el aviso de privacidad.", "error")
            return redirect(url_for('register'))

        try:
            # Conectar a la base de datos
            connection = get_db_connection()
            if connection is None:
                flash("Error al conectar a la base de datos", "error")
                return redirect(url_for('register'))

            cursor = connection.cursor(dictionary=True)

            # Verificar si el correo ya existe en alguna de las tablas (Usuarios o Usuarios_Google)
            cursor.execute("""
                SELECT 'Usuarios' AS source FROM Usuarios WHERE correo = %s 
                UNION ALL 
                SELECT 'Usuarios_Google' AS source FROM Usuarios_Google WHERE correo = %s
            """, (email, email))

            usuario_existente = cursor.fetchone()

            if usuario_existente:
                if usuario_existente["source"] == "Usuarios":
                    flash("El correo ya está registrado como usuario normal.", "error")
                elif usuario_existente["source"] == "Usuarios_Google":
                    flash("El correo ya está registrado con Google. Inicia sesión con Google.", "error")
                return redirect(url_for('register'))  # Evita continuar con el registro

            # Solo si el usuario NO existe, se asignan las variables globales y se envía el PIN
            correo_usuario = email
            nombre_usuario = nombre

            flash("Registro exitoso. Se ha enviado un PIN a tu correo.", "success")
            return envio_pin()

        except mysql.connector.Error as e:
            print(f"Error al verificar usuario: {e}")
            flash("Error en el registro. Intenta nuevamente.", "error")
            return redirect(url_for('register'))

        finally:
            if cursor:
                cursor.fetchall()  # Evita errores con cursores abiertos
                cursor.close()
            if connection:
                connection.close()

    return render_template('Register.html')

# Ruta para terminos y condiciones
@app.route('/terminos', methods=['GET', 'POST'])
def terminos():
      return render_template('Terminos_Condiciones.html')

# Ruta para aviso de privacidad
@app.route('/privacidad', methods=['GET', 'POST'])
def privacidad():
    return render_template('Aviso_Privacidad.html')

@app.route('/envio_pin', methods=['POST'])
def envio_pin():
    global pin, pin_timestamp, correo_usuario  # Asegurar que usa las variables globales

    if not correo_usuario:
        return jsonify({"error": "Correo no proporcionado"}), 400

    pin = generar_pin()  # Generar el PIN
    pin_timestamp = time.time()  # Guardar el tiempo de generación del PIN

    # Cargar y modificar el HTML con el PIN
    ruta_html = os.path.join(RUTA_CARPETA, ARCHIVO_HTML)
    html_modificado = cargar_y_modificar_html(ruta_html, pin)

    if html_modificado:
        enviar_correo(REMITENTE, CONTRASEÑA, correo_usuario, "Código de Verificación", html_modificado)
        return redirect(url_for('validacion', correo=correo_usuario))
    else:
        return jsonify({"error": "No se pudo cargar la plantilla HTML"}), 500

# Funcion de reenvio de PIN por si no le llego, pero es mas para cuando puso mal el correo
@app.route('/reenvio/<destino>', methods=['GET','POST'])
def reenvio(destino):
    global pin, pin_timestamp, correo_usuario  # Asegurar que usa las variables globales

    if not correo_usuario:
        return jsonify({"error": "Correo no proporcionado"}), 400

    pin = generar_pin()  # Generar el PIN
    pin_timestamp = time.time()  # Guardar el tiempo de generación del PIN

    # Cargar y modificar el HTML con el PIN
    ruta_html = os.path.join(RUTA_CARPETA, ARCHIVO_HTML)
    html_modificado = cargar_y_modificar_html(ruta_html, pin)

    if html_modificado:
        enviar_correo(REMITENTE, CONTRASEÑA, correo_usuario, "Código de Verificación", html_modificado)
        return redirect(url_for('validacion', correo=correo_usuario))
    else:
        return jsonify({"error": "No se pudo cargar la plantilla HTML"}), 500

# Funcion para la validacion del PIN
@app.route('/validacion', methods=['GET', 'POST'])
def validacion():
    global pin, pin_timestamp, correo_usuario
    
    correo = request.args.get('correo')  # Obtener el correo desde los parámetros de la URL
    if not correo:  # Verificar si no se recibe el correo
        flash("Correo no proporcionado.", "error")
        return redirect(url_for('register'))
    print(correo_usuario)

    if request.method == 'POST':
        pin_ingresado = request.form.get('pin')  # Captura el PIN ingresado

        # Validar que el PIN no esté vacío
        if not pin_ingresado:
            flash("Por favor ingrese el PIN.", "error")
            return redirect(url_for('validacion', correo=correo))
        
        # Verificar si el PIN es correcto y aún no ha expirado
        if pin_ingresado == pin and (time.time() - pin_timestamp) <= PIN_EXPIRATION_SECONDS:
            return redirect(url_for('contrasena', correo=correo))
        else:
            flash("PIN incorrecto o expirado.", "error")
        
    return render_template('Validacion.html', correo=correo)

# Funcion para colocar la contraseña de acceso del usuario
# Modificar para que sea mas simple
# Poner update si es olvide contraseña
@app.route('/contrasena', methods=['GET', 'POST']) 
def contrasena():
    global nombre_usuario, correo_usuario  # Usamos las variables globales para el nombre y correo

    if not nombre_usuario or not correo_usuario:
        print("Nombre o correo no proporcionado")
        message = "Nombre o correo no proporcionado"
        message_color = "red"
        return render_template('Password.html', message=message, message_color=message_color)

    print(f"Correo recibido: {correo_usuario}, Nombre recibido: {nombre_usuario}")
    cursor = None
    connection = None

    if request.method == 'POST':
        nueva_contrasena = request.form.get('password')
        confirmar_contrasena = request.form.get('confirm-password')

        if nueva_contrasena != confirmar_contrasena:
            message = "Las contraseñas no coinciden"
            message_color = "red"
            return render_template('Password.html', correo=correo_usuario, message=message, message_color=message_color)

        if len(nueva_contrasena) < 8:
            message = "La contraseña debe tener al menos 8 caracteres"
            message_color = "red"
            return render_template('Password.html', correo=correo_usuario, message=message, message_color=message_color)

        try:
            hashed_password = generate_password_hash(nueva_contrasena)
            print(f"Contraseña hasheada: {hashed_password}")

            connection = mysql.connector.connect(**DB_CONFIG)
            cursor = connection.cursor()
            print("Conexión a la base de datos establecida")

            # Verificar si el usuario ya existe
            query_check = "SELECT id_usuario FROM Usuarios WHERE correo = %s"
            cursor.execute(query_check, (correo_usuario,))
            resultado = cursor.fetchone()
            cursor.fetchall()  # <- AÑADIDO para evitar el error 'Unread result found'

            if resultado:
                # Usuario ya existe → actualizar contraseña
                query_update = "UPDATE Usuarios SET contrasena = %s WHERE correo = %s"
                cursor.execute(query_update, (hashed_password, correo_usuario))
                connection.commit()
                print("Contraseña actualizada para usuario existente")
                return redirect('/', code=302)
            else:
                # Usuario no existe → insertar nuevo registro
                query_insert = """
                    INSERT INTO Usuarios (
                        foto_perfil, nombre, apellidos, correo, contrasena, telefono,
                        direccion, fecha_nacimiento, tipo_perfil, horas_adquiridas,
                        horas_usadas, institucion, id_dispositivo
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                valores = (
                    None, nombre_usuario, None, correo_usuario, hashed_password, None, None, None,
                    "usuario", 0, 0, None, None
                )
                cursor.execute(query_insert, valores)
                connection.commit()
                print("Usuario registrado con nueva contraseña")
                return redirect('/', code=302)

        except mysql.connector.Error as err:
            print(f"Error en la base de datos: {err}")
            message = f"Error en la base de datos: {err}"
            message_color = "red"
            return render_template('Password.html', correo=correo_usuario, message=message, message_color=message_color)

        finally:
            if cursor:
                cursor.close()
                print("Cursor cerrado")
            if connection:
                connection.close()
                print("Conexión cerrada")

    # Si es GET, renderiza el formulario
    print("Método GET, mostrando formulario con correo")
    return render_template('Password.html', correo=correo_usuario)
# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Funcion para el olvido de contraseña y se quiere restablecer
@app.route("/olvido", methods=['GET', 'POST'])
def olvido():
    global correo_usuario, nombre_usuario  # Asegurar que usa la variable global

    if request.method == 'POST':
        correo_usuario = request.form.get('email')
        print(correo_usuario)
        nombre_usuario = "usuario_temp"

        if not correo_usuario:
            return jsonify({"error": "Correo no proporcionado"}), 400

        return envio_pin()  # Llama a la función existente para enviar el PIN

    # Si es GET, mostrar el formulario para ingresar el correo
    return render_template('olvido.html')


# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Función para entrar al home de la página
# ver la forma de tomar las reservaciones y cambiar lo de microsft tanto nombre como imagen
@app.route('/home', methods=['GET', 'POST'])
def home():
    global nombre_usuario, usuario_google, usuario_normal, id_usuario_global

    # 🔒 Verificación de autenticación
    if not (usuario_google or usuario_normal):
        return redirect(url_for('login'))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Obtener la fecha y hora local utilizando la función obtener_ubicacion_y_hora()
        info_local = obtener_ubicacion_y_hora()
        fecha_local = info_local["fecha_local"]
        hora_local = info_local["hora_local"]
        fecha_hora_local = f"{fecha_local} {hora_local}"

        # 🔹 Determinar filtro según tipo de usuario
        if usuario_normal:
            filtro_usuario = "id_usuario = %s"
            valor_usuario = id_usuario_global
        elif usuario_google:
            filtro_usuario = "id_usuario_google = %s"
            valor_usuario = id_usuario_global

        # 🔹 Actualizar reservas vencidas a 'caducado' si la fecha_reserva es menor a la fecha actual
        cursor.execute(f"""
            UPDATE Reservas
            SET estado_reserva = 'caducado'
            WHERE {filtro_usuario} 
            AND estado_reserva = 'activo'
            AND DATE(fecha_reserva) < %s
        """, (valor_usuario, fecha_local))
        connection.commit()

        # 🔹 Obtener la suma total de horas utilizadas (Horas Activas)
        cursor.execute(f"""
            SELECT COALESCE(SUM(horas_utilizadas), 0) AS horas_activas 
            FROM HorasPaquete 
            WHERE {filtro_usuario}
        """, (valor_usuario,))
        horas_activas = cursor.fetchone()["horas_activas"]

        # 🔹 Calcular el promedio de horas utilizadas en la última semana
        cursor.execute(f"""
            SELECT COALESCE(ROUND(AVG(horas_utilizadas), 1), 0) AS promedio_horas
            FROM HorasPaquete
            WHERE {filtro_usuario} 
            AND fecha_pago >= %s
        """, (valor_usuario, fecha_hora_local))
        promedio_horas = cursor.fetchone()["promedio_horas"]

        print(nombre_usuario)
        print(horas_activas)
        print(promedio_horas)

    except mysql.connector.Error as e:
        print(f"Error en la base de datos: {e}")
        horas_activas, promedio_horas = 0, 0

    finally:
        cursor.close()
        connection.close()

    # Renderizar la página
    return render_template('home.html', user=nombre_usuario, horas_activas=horas_activas, promedio_horas=promedio_horas)

# Funcion de los productos de la tienda
@app.route('/tienda', methods=['POST', 'GET'])
def tienda():
    global usuario_google, usuario_normal

    # 🔒 Verificación de autenticación
    if not (usuario_google or usuario_normal):
        return redirect(url_for('login'))

    return render_template('tienda.html')

@app.route('/paquetes')
def paquetes():
    global usuario_google, usuario_normal, id_usuario_global

    if not (usuario_google or usuario_normal):
        return redirect(url_for('login'))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Determinar el filtro de usuario según el tipo de usuario
        if usuario_google:
            filtro_usuario = "id_usuario_google = %s"
        else:
            filtro_usuario = "id_usuario = %s"

        # Verificar si el usuario ha realizado un pago antes
        cursor.execute(f"SELECT COUNT(*) as total FROM Pagos WHERE {filtro_usuario}", (id_usuario_global,))
        resultado = cursor.fetchone()
        primera_compra = resultado["total"] == 0  # Si el total es 0, significa que nunca ha comprado

        # Consultar los paquetes con los campos solicitados
        cursor.execute("""SELECT precio, moneda, horas, caducacion, nombre_paquete FROM Paquetes""")
        paquetes = cursor.fetchall()  # Esto obtendrá todos los registros de paquetes
        
        # Devolver los paquetes y la información sobre la primera compra
        return render_template('paquetes.html', 
                               primera_compra=primera_compra, 
                               paquetes=paquetes)

    except mysql.connector.Error as e:
        return jsonify({"error": f"Error en la base de datos: {str(e)}"}), 500
    finally:
        cursor.close()
        connection.close()
# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Funcion para las reservaciones cambiar
# Cambiar para que distinga entre usuario normal y google y verifique disponibilidad de fecha y hora
# Cambiar para que acepte el forma de fecha y hora del frontend
@app.route('/reservacion', methods=['GET', 'POST'])
def reservacion():
    global usuario_normal, usuario_google, id_usuario_global

    if not (usuario_normal or usuario_google):
        return redirect(url_for('login'))

    if request.method == 'POST':
        data = request.get_json()
        fecha = data.get('fecha')
        hora = data.get('hora')
        duracion = data.get('duracion')

        print("Datos recibidos:", data)

        if not fecha or not hora or not duracion:
            return jsonify({"success": False, "error": "Todos los campos son obligatorios"}), 400

        try:
            duracion = int(duracion)
            if ":" not in hora:
                hora = f"{hora}:00"

            fecha_reserva = datetime.strptime(f"{fecha} {hora}:00", "%Y-%m-%d %H:%M:%S")
            fecha_finalizacion = fecha_reserva + timedelta(hours=duracion)

            print(f"Reserva solicitada de {duracion} horas:")
            print("Inicio:", fecha_reserva)
            print("Fin:", fecha_finalizacion)

        except ValueError:
            return jsonify({"success": False, "error": "Formato de fecha u hora inválido"}), 400

        ubicacion_y_hora = obtener_ubicacion_y_hora()
        location_full = ubicacion_y_hora["ubicacion_completa"]
        fecha_registro = ubicacion_y_hora["fecha_local"] + " " + ubicacion_y_hora["hora_local"]

        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            connection.start_transaction()

            if usuario_normal:
                filtro_usuario = "id_usuario = %s"
                valor_usuario = id_usuario_global
                id_usuario_insert = id_usuario_global
                id_usuario_google_insert = None
                print("Usuario normal:", id_usuario_global)
            elif usuario_google:
                filtro_usuario = "id_usuario_google = %s"
                valor_usuario = id_usuario_global
                id_usuario_insert = None
                id_usuario_google_insert = id_usuario_global
                print("Usuario Google:", id_usuario_global)

            # Buscar máquina disponible
            maquina_asignada = None
            for maquina in [1, 2]:
                cursor.execute("""
                    SELECT fecha_reserva, duracion 
                    FROM Reservas 
                    WHERE DATE(fecha_reserva) = %s AND estado_reserva = 'Activo' AND maquina = %s
                """, (fecha, maquina))
                reservas = cursor.fetchall()

                conflicto = False
                for r in reservas:
                    inicio = r['fecha_reserva']
                    fin = inicio + timedelta(hours=r['duracion'])
                    if (fecha_reserva < fin and fecha_finalizacion > inicio):
                        conflicto = True
                        break

                if not conflicto:
                    maquina_asignada = maquina
                    print(f"Máquina asignada: {maquina_asignada}")
                    break

            if not maquina_asignada:
                connection.rollback()
                print("No hay máquinas disponibles")
                return jsonify({"success": False, "error": "No hay disponibilidad en ninguna máquina para esa fecha y hora"}), 400

            # Buscar pagos válidos
            cursor.execute(f"""
                SELECT p.id_pago, p.id_paquete 
                FROM Pagos p
                WHERE p.estado = 'paid' AND p.estado_paquete = 'no consumido' AND {filtro_usuario}
                ORDER BY p.fecha_pago ASC
            """, (valor_usuario,))
            pagos_validos = cursor.fetchall()
            print("Pagos válidos encontrados:", pagos_validos)

            paquete_seleccionado = None

            for pago in pagos_validos:
                id_pago = pago['id_pago']
                id_paquete = pago['id_paquete']
                print(f"Evaluando id_pago: {id_pago}, id_paquete: {id_paquete}")

                # Verificar si tiene registro en HorasPaquete
                cursor.execute("""
                    SELECT id_paquete, horas_totales, horas_utilizadas, 
                           (horas_totales - horas_utilizadas) AS horas_restantes
                    FROM HorasPaquete 
                    WHERE id_pago = %s AND id_paquete = %s
                """, (id_pago, id_paquete))
                horas_registro = cursor.fetchone()

                if horas_registro:
                    print("Horas encontradas en HorasPaquete:", horas_registro)
                    if horas_registro['horas_restantes'] >= duracion:
                        print("Este paquete puede cubrir la duración.")
                        paquete_seleccionado = {
                            "id_pago": id_pago,
                            "id_paquete": id_paquete
                        }
                        break
                    else:
                        print("No tiene suficientes horas restantes.")
                else:
                    # No tiene horas registradas aún, buscar en Paquetes
                    cursor.execute("""
                        SELECT horas FROM Paquetes WHERE id_paquete = %s
                    """, (id_paquete,))
                    paquete_info = cursor.fetchone()
                    if paquete_info:
                        print("Horas disponibles desde paquete base:", paquete_info['horas'])
                        if paquete_info['horas'] >= duracion:
                            print("Este paquete puede cubrir la duración desde Paquetes.")
                            paquete_seleccionado = {
                                "id_pago": id_pago,
                                "id_paquete": id_paquete
                            }
                            break
                    else:
                        print("No se encontró información del paquete.")

            if not paquete_seleccionado:
                connection.rollback()
                print("No hay paquetes que cubran la duración solicitada.")
                return jsonify({"success": False, "error": "No tienes suficientes horas para completar esta reserva"}), 400

            # Insertar reserva
            cursor.execute("""
                INSERT INTO Reservas (
                    fecha_reserva, duracion, fecha_registro, estado_reserva, 
                    maquina, ubicacion, id_usuario, id_usuario_google, 
                    id_pago, id_paquete, tiempo_solicitado, fecha_finalizacion
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                fecha_reserva, duracion, fecha_registro, "pendiente",
                maquina_asignada, location_full,
                id_usuario_insert, id_usuario_google_insert,
                paquete_seleccionado['id_pago'], paquete_seleccionado['id_paquete'],
                duracion,fecha_finalizacion  # El tiempo solicitado es igual a la duración solicitada
            ))

            id_reserva = cursor.lastrowid
            connection.commit()
            print("Reserva registrada correctamente con ID:", id_reserva)

            return jsonify({
                "success": True,
                "message": "Reserva registrada en estado pendiente",
                "estado": "pendiente",
                "duracion": duracion,
                "id_reserva": id_reserva
            }), 200

        except Exception as e:
            connection.rollback()
            print(f"Error al registrar la reserva: {e}")
            return jsonify({"success": False, "error": "Error al registrar la reserva"}), 500

        finally:
            cursor.close()
            connection.close()

    return render_template("reservacion.html")


@app.route("/confirmar_reservacion", methods=["POST"])
def confirmar_reservacion():
    global usuario_normal, usuario_google, id_usuario_global
    data = request.json
    print(data)
    duracion = data.get("duracion")
    id_reserva = data.get("id_reserva")  # ✅ nueva variable

    if not duracion or not id_reserva:
        return jsonify({"success": False, "error": "Faltan parámetros"}), 400

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Autenticación con variables globales
        if usuario_normal:
            filtro_usuario = "id_usuario = %s"
            valor_usuario = id_usuario_global
            id_usuario_insert = id_usuario_global
            id_usuario_google_insert = None
            print("Usuario normal:", id_usuario_global)
        elif usuario_google:
            filtro_usuario = "id_usuario_google = %s"
            valor_usuario = id_usuario_global
            id_usuario_insert = None
            id_usuario_google_insert = id_usuario_global
            print("Usuario Google:", id_usuario_global)
        else:
            return jsonify({"success": False, "error": "No autenticado"}), 401

        cursor.execute(f"""
            SELECT id_pago, id_paquete, fecha_pago, fecha_caducidad 
            FROM Pagos 
            WHERE estado = 'paid' AND estado_paquete = 'no consumido' 
            AND {filtro_usuario}
            ORDER BY fecha_pago ASC
        """, (valor_usuario,))
        paquetes = cursor.fetchall()

        if not paquetes:
            connection.rollback()
            return jsonify({"success": False, "error": "No tienes paquetes válidos"}), 400

        horas_necesarias = duracion
        id_paquete_reserva = None
        id_pago_reserva = None

        for paquete in paquetes:
            id_pago = paquete['id_pago']
            id_paquete = paquete['id_paquete']
            fecha_pago = paquete['fecha_pago']
            fecha_caducidad = paquete['fecha_caducidad']

            cursor.execute("SELECT * FROM HorasPaquete WHERE id_pago = %s", (id_pago,))
            hp = cursor.fetchone()

            if hp:
                disponibles = hp['horas_totales'] - hp['horas_utilizadas']
                if disponibles <= 0:
                    continue

                if horas_necesarias <= disponibles:
                    cursor.execute("""
                        UPDATE HorasPaquete 
                        SET horas_utilizadas = horas_utilizadas + %s 
                        WHERE id_pago = %s
                    """, (horas_necesarias, id_pago))
                    if horas_necesarias == disponibles:
                        cursor.execute("UPDATE Pagos SET estado_paquete = 'consumido' WHERE id_pago = %s", (id_pago,))
                    id_paquete_reserva = id_paquete
                    id_pago_reserva = id_pago
                    horas_necesarias = 0
                    break
                else:
                    cursor.execute("""
                        UPDATE HorasPaquete 
                        SET horas_utilizadas = horas_utilizadas + %s 
                        WHERE id_pago = %s
                    """, (disponibles, id_pago))
                    cursor.execute("UPDATE Pagos SET estado_paquete = 'consumido' WHERE id_pago = %s", (id_pago,))
                    horas_necesarias -= disponibles
            else:
                cursor.execute("SELECT horas FROM Paquetes WHERE id_paquete = %s", (id_paquete,))
                info_paquete = cursor.fetchone()
                if not info_paquete:
                    continue

                horas_totales = info_paquete['horas']
                if horas_necesarias <= horas_totales:
                    cursor.execute("""
                        INSERT INTO HorasPaquete (id_pago, id_paquete, horas_totales, horas_utilizadas, fecha_pago, fecha_caducidad, id_usuario, id_usuario_google)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (id_pago, id_paquete, horas_totales, horas_necesarias, fecha_pago, fecha_caducidad, id_usuario_insert, id_usuario_google_insert))
                    if horas_necesarias == horas_totales:
                        cursor.execute("UPDATE Pagos SET estado_paquete = 'consumido' WHERE id_pago = %s", (id_pago,))
                    id_paquete_reserva = id_paquete
                    id_pago_reserva = id_pago
                    horas_necesarias = 0
                    break
                else:
                    cursor.execute("""
                        INSERT INTO HorasPaquete (id_pago, id_paquete, horas_totales, horas_utilizadas, fecha_pago, fecha_caducidad, id_usuario, id_usuario_google)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (id_pago, id_paquete, horas_totales, horas_totales, fecha_pago, fecha_caducidad, id_usuario_insert, id_usuario_google_insert))
                    cursor.execute("UPDATE Pagos SET estado_paquete = 'consumido' WHERE id_pago = %s", (id_pago,))
                    horas_necesarias -= horas_totales

        # Marcar paquetes como consumidos si ya no tienen horas restantes
        cursor.execute("""
            SELECT id_pago 
            FROM HorasPaquete 
            WHERE horas_restantes = 0
        """)
        pagos_consumidos = cursor.fetchall()

        for pago in pagos_consumidos:
            id_pago_consumido = pago['id_pago']
            cursor.execute("UPDATE Pagos SET estado_paquete = 'consumido' WHERE id_pago = %s", (id_pago_consumido,))

        if horas_necesarias > 0:
            connection.rollback()
            return jsonify({"success": False, "error": "No tienes suficientes horas para completar esta reserva"}), 400

        # ✅ Actualizar estado_reserva a "Activo"
        cursor.execute("""
            UPDATE Reservas SET estado_reserva = 'Activo' WHERE id_reserva = %s
        """, (id_reserva,))

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Reserva confirmada",
            "id_pago": id_pago_reserva,
            "id_paquete": id_paquete_reserva
        }), 200

    except Exception as e:
        connection.rollback()
        print("Error en la reserva:", str(e))
        return jsonify({"success": False, "error": "Error interno"}), 500

    finally:
        cursor.close()
        connection.close()

@app.route('/eliminar_reserva/<int:id_reserva>', methods=['DELETE'])
def eliminar_reserva(id_reserva):
    # Abrir conexión a la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()

    # Primero verificar si la reserva existe y si está pendiente
    cursor.execute("SELECT * FROM Reservas WHERE id_reserva = %s", (id_reserva,))
    reserva = cursor.fetchone()
    print(reserva)

    if not reserva:
        conn.close()
        return jsonify({"error": "Reserva no encontrada"}), 404

    if reserva[9] != 'pendiente':
        conn.close()
        return jsonify({"error": "Solo se pueden eliminar reservas con estatus 'pendiente'"}), 400

    # Si la reserva está pendiente, eliminamos la reserva
    try:
        cursor.execute("DELETE FROM Reservas WHERE id_reserva = %s", (id_reserva,))
        conn.commit()  # Confirmamos los cambios
        conn.close()
        return jsonify({"message": "Reserva eliminada con éxito"}), 200
    except Exception as e:
        conn.close()
        return jsonify({"error": f"Error al eliminar la reserva: {str(e)}"}), 500
# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/horas_disponibles', methods=['GET'])
def horas_disponibles():
    global usuario_normal, usuario_google, id_usuario_global
    print(id_usuario_global)

    if not (usuario_normal or usuario_google):
        return jsonify({"success": False, "error": "Usuario no autenticado"}), 400

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # 1️⃣ Determinar filtro según tipo de usuario
        if usuario_normal:
            filtro_usuario = "id_usuario = %s"
            valor_usuario = id_usuario_global
        elif usuario_google:
            filtro_usuario = "id_usuario_google = %s"
            valor_usuario = id_usuario_global
        else:
            return jsonify({"success": False, "error": "Usuario no identificado"}), 400

        # 2️⃣ Buscar todos los pagos con estado 'paid' y 'no consumido'
        cursor.execute(f"""
            SELECT id_pago, id_paquete, fecha_caducidad 
            FROM Pagos 
            WHERE estado = 'paid' AND estado_paquete = 'no consumido'
            AND {filtro_usuario}
        """, (valor_usuario,))
        pagos = cursor.fetchall()

        if not pagos:
            return jsonify({"success": False, "error": "No tienes horas disponibles. Ve a la sección de paquetes."}), 400

        total_horas = 0
        pagos_a_consumir = []

        # 3️⃣ Sumar las horas de HorasPaquete y detectar paquetes sin horas
        for pago in pagos:
            id_pago = pago['id_pago']
            id_paquete = pago['id_paquete']
            fecha_caducidad_pago = pago['fecha_caducidad']

            # Verificar si la fecha_caducidad en Pagos es hoy y actualizar estado a 'caducado'
            if fecha_caducidad_pago == date.today():
                cursor.execute("UPDATE Pagos SET estado_paquete = 'caducado' WHERE id_pago = %s", (id_pago,))
                connection.commit()

            # Consultar las horas restantes en HorasPaquete
            cursor.execute("SELECT horas_restantes, fecha_caducidad FROM HorasPaquete WHERE id_pago = %s", (id_pago,))
            horas_paquete = cursor.fetchone()

            # Verificar si la fecha_caducidad en HorasPaquete es hoy, aunque haya horas restantes
            if horas_paquete and horas_paquete['fecha_caducidad'] == date.today():
                cursor.execute("UPDATE HorasPaquete SET estado_paquete = 'caducado' WHERE id_pago = %s", (id_pago,))
                connection.commit()

            if horas_paquete:
                horas_restantes = horas_paquete['horas_restantes']
                total_horas += horas_restantes

                # Si un paquete tiene 0 horas restantes, marcarlo como 'consumido'
                if horas_restantes == 0:
                    pagos_a_consumir.append(id_pago)
            else:
                # Si no hay horas en HorasPaquete, consultar en Paquetes
                cursor.execute("SELECT horas FROM Paquetes WHERE id_paquete = %s", (id_paquete,))
                paquete = cursor.fetchone()

                if paquete:
                    total_horas += paquete['horas']

        # 4️⃣ Cambiar estado a 'consumido' si es necesario
        if pagos_a_consumir:
            cursor.executemany("UPDATE Pagos SET estado_paquete = 'consumido' WHERE id_pago = %s", [(id_pago,) for id_pago in pagos_a_consumir])
            connection.commit()

        # 5️⃣ Si no hay horas disponibles, enviar error
        if total_horas == 0:
            return jsonify({"success": False, "error": "No tienes horas disponibles. Ve a la sección de paquetes."}), 400

        # 6️⃣ Devolver el total de horas restantes
        return jsonify({"success": True, "horas_restantes": total_horas})

    except mysql.connector.Error as e:
        return jsonify({"success": False, "error": f"Error en BD: {e}"}), 500
    finally:
        cursor.close()
        connection.close()


@app.route("/reservas_cercanas", methods=["GET"])
def obtener_reservas_cercanas():
    global id_usuario_global, usuario_normal, usuario_google  # Variables globales dentro de la función

    connection = get_db_connection()  
    if connection is None:
        return jsonify({"success": False, "error": "No se pudo conectar a la base de datos"}), 500

    cursor = connection.cursor(dictionary=True)

    try:
        # 📌 Determinar el tipo de usuario y aplicar filtro
        if usuario_normal:
            filtro_usuario = "id_usuario = %s"
        elif usuario_google:
            filtro_usuario = "id_usuario_google = %s"
        else:
            return jsonify({"success": False, "error": "Usuario no identificado"}), 400

        # 🕒 Obtener fecha y hora actual
        fecha_actual = datetime.now()

        print(f"🔍 Consultando reservas para usuario ID: {id_usuario_global} - Fecha actual: {fecha_actual}")

        # 1️⃣ CONTAR RESERVAS A CAMBIAR A "inactivo"
        cursor.execute(f"""
            SELECT COUNT(*) as total_cambio
            FROM Reservas 
            WHERE {filtro_usuario} 
            AND estado_reserva = 'activo' 
            AND DATE_ADD(fecha_reserva, INTERVAL duracion HOUR) < %s
        """, (id_usuario_global, fecha_actual))
        total_cambio = cursor.fetchone()["total_cambio"]

        print(f"⚠️ Reservas cambiadas a 'inactivo': {total_cambio}")

        # 2️⃣ ACTUALIZAR RESERVAS VENCIDAS A "inactivo"
        cursor.execute(f"""
            UPDATE Reservas 
            SET estado_reserva = 'inactivo' 
            WHERE {filtro_usuario} 
            AND estado_reserva = 'activo' 
            AND DATE_ADD(fecha_reserva, INTERVAL duracion HOUR) < %s
        """, (id_usuario_global, fecha_actual))
        connection.commit()
        print("✅ Reservas vencidas actualizadas correctamente.")

        # 3️⃣ OBTENER LAS 3 RESERVAS MÁS CERCANAS
        cursor.execute(f"""
            SELECT fecha_reserva, duracion, 
                DATE_FORMAT(fecha_reserva, '%d/%m/%Y') AS fecha_formateada,
                DATE_FORMAT(fecha_reserva, '%I:%i %p') AS hora_inicio,
                DATE_FORMAT(DATE_ADD(fecha_reserva, INTERVAL duracion HOUR), '%I:%i %p') AS hora_fin
            FROM Reservas
            WHERE {filtro_usuario} 
            AND estado_reserva = 'activo' 
            ORDER BY fecha_reserva ASC 
            LIMIT 3
        """, (id_usuario_global,))
        
        reservas = cursor.fetchall()

        print("📌 Próximas 3 reservas activas:")
        for reserva in reservas:
            print(f"📅 {reserva['fecha_formateada']} ⏰ {reserva['hora_inicio']} - {reserva['hora_fin']}")

        return jsonify({"success": True, "reservas": reservas, "cambiadas": total_cambio})

    except mysql.connector.Error as e:
        print(f"❌ Error en la base de datos: {e}")
        return jsonify({"success": False, "error": f"Error en la base de datos: {e}"}), 500

    finally:
        cursor.close()
        connection.close()
        print("🔌 Conexión cerrada.")

#Se hara el token de acuerdo a este formato Distintivo numero de workspace-Nombre Usuario o ID- fecha - hora -  duracion de la reservacion
#Se pondra en la bd con ID, ID_usuario o ID_usuario_google, ID_reservacion, y el token hasheado
#falta implementacion y verificar una cosas
@app.route('/reservas_page')
def reservas_page():
    global id_usuario_global, usuario_normal, usuario_google

    # 🔒 Verificación de autenticación
    if not (usuario_normal or usuario_google):
        return redirect(url_for('login'))

    # Determinar el tipo de usuario y aplicar filtro
    if usuario_normal:
        filtro_usuario = "id_usuario = %s"
    elif usuario_google:
        filtro_usuario = "id_usuario_google = %s"
    else:
        return redirect(url_for('login'))

    # Conectar a la base de datos
    conn = get_db_connection()
    if conn is None:
        return render_template('error.html', mensaje="No se pudo conectar a la base de datos")

    cursor = conn.cursor(dictionary=True)

    try:
        # Consultar la tabla Reservas para obtener las reservas activas del usuario
        query = f"""
        SELECT id_reserva, fecha_reserva, duracion, estado_reserva
        FROM Reservas
        WHERE {filtro_usuario} AND estado_reserva = 'Activo'
        """
        cursor.execute(query, (id_usuario_global,))
        
        resultados = cursor.fetchall()

        if resultados:
            return render_template('reservas.html', reservas=resultados)
        else:
            return render_template('reservas.html', reservas=[], mensaje="No se encontraron reservas activas.")
    except Exception as e:
        return render_template('error.html', mensaje=f"Ocurrió un error: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Función para generar el hash del token
def hash_token(token):
    # Usamos SHA-256 para hashear el token
    sha256_hash = hashlib.sha256()
    sha256_hash.update(token.encode('utf-8'))
    return sha256_hash.hexdigest()

@app.route('/token', methods=['POST'])
def generar_token():
    global id_usuario_global, usuario_normal, usuario_google

    # 🔒 Verificar si el usuario está autenticado, de lo contrario redirigir a login
    if not (usuario_normal or usuario_google):
        return redirect(url_for('login'))

    if not id_usuario_global:
        return jsonify({"success": False, "error": "Usuario no identificado"}), 400

    # Obtener datos del JSON enviado desde el frontend
    data = request.get_json()
    id_reserva = data.get("id_reserva")

    if not id_reserva:
        return jsonify({"success": False, "error": "ID de reserva no proporcionado"}), 400

    # 📌 Determinar el filtro y el tipo de usuario
    if usuario_normal:
        filtro_usuario = "id_usuario = %s"
        usuario_id = id_usuario_global
    elif usuario_google:
        filtro_usuario = "id_usuario_google = %s"
        usuario_id = id_usuario_global
    else:
        return jsonify({"success": False, "error": "Tipo de usuario no identificado"}), 400

    # Conectar a la base de datos
    conn = get_db_connection()
    if conn is None:
        return jsonify({"success": False, "error": "No se pudo conectar a la base de datos"}), 500

    cursor = conn.cursor(dictionary=True)

    try:
        # Verificar que la reserva exista, sea del usuario, y esté activa
        query = f"""
        SELECT id_reserva, fecha_reserva, duracion
        FROM Reservas
        WHERE {filtro_usuario} AND id_reserva = %s AND estado_reserva = 'Activo'
        """
        cursor.execute(query, (usuario_id, id_reserva))
        resultados = cursor.fetchall()

        if not resultados:
            return jsonify({'error': 'Reserva no encontrada o no activa'}), 404

        reserva = resultados[0]
        fecha_reserva = reserva['fecha_reserva']
        fecha_str = fecha_reserva.strftime('%Y-%m-%d')
        hora_str = fecha_reserva.strftime('%H:%M:%S')
        duracion = reserva['duracion']

        # 🔐 Generar y hashear el token
        token = f"T-{reserva['id_reserva']}-{id_usuario_global}-{fecha_str}-{hora_str}-{duracion}"
        hashed_token = hash_token(token)

        # Verificar si ya existe un token para esta reserva
        check_token_query = f"""
        SELECT token FROM Tokens WHERE id_reserva = %s AND {filtro_usuario}
        """
        cursor.execute(check_token_query, (id_reserva, usuario_id))
        existing_token = cursor.fetchone()

        if existing_token:
            return jsonify({'hashed_token': existing_token['token']})

        # Obtener ubicación y fecha de creación del token
        info_local = obtener_ubicacion_y_hora()
        ubicacion = info_local["ubicacion_completa"]
        fecha_creacion = f"{info_local['fecha_local']} {info_local['hora_local']}"

        # Insertar nuevo token
        insert_query = """
        INSERT INTO Tokens (id_usuario, id_usuario_google, id_reserva, token, fecha_creacion, ubicacion)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (
            id_usuario_global if usuario_normal else None,
            id_usuario_global if usuario_google else None,
            id_reserva,
            hashed_token,
            fecha_creacion,
            ubicacion
        ))
        conn.commit()

        return jsonify({'hashed_token': hashed_token})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Funcion para modificar perfil
@app.route('/perfil', methods=['GET', 'POST'])
def perfil():
    global id_usuario_global, usuario_normal, usuario_google

    if not (usuario_normal or usuario_google) or not id_usuario_global:
        return redirect(url_for('login'))

    conn = get_db_connection()
    if not conn:
        return "Error al conectar con la base de datos"

    cursor = conn.cursor()

    if request.method == 'POST':
        # Obtener datos del formulario
        nombre = request.form.get('nombre')
        apellidos = request.form.get('apellidos')
        correo = request.form.get('correo')
        telefono = request.form.get('telefono')
        direccion = request.form.get('direccion')
        fecha_nacimiento = request.form.get('fecha_nacimiento')
        tipo_perfil = request.form.get('tipo_perfil')
        institucion = request.form.get('institucion')
        foto = request.files.get('foto')

        if usuario_normal:
            if foto and foto.filename != '':
                try:
                    # Procesar la imagen con Pillow
                    imagen = Image.open(foto)
                    print(f"Imagen cargada correctamente: {foto.filename}")
                    img_io = io.BytesIO()
                    imagen = imagen.convert('RGB')  # Asegúrate de convertirla a RGB si no lo está
                    imagen.save(img_io, 'JPEG')  # Guardarla en formato JPEG o el que prefieras
                    img_io.seek(0)
                    foto_blob = img_io.read()
                    print(f"Imagen procesada correctamente en formato BLOB")
                    
                    cursor.execute("""
                        UPDATE Usuarios
                        SET nombre=%s, apellidos=%s, correo=%s, telefono=%s, direccion=%s,
                            fecha_nacimiento=%s, tipo_perfil=%s, institucion=%s, foto_perfil=%s
                        WHERE id_usuario = %s
                    """, (nombre, apellidos, correo, telefono, direccion,
                          fecha_nacimiento, tipo_perfil, institucion, foto_blob, id_usuario_global))
                except Exception as e:
                    print(f"Error al procesar la imagen: {e}")
                    return "Error al procesar la imagen."
            else:
                cursor.execute("""
                    UPDATE Usuarios
                    SET nombre=%s, apellidos=%s, correo=%s, telefono=%s, direccion=%s,
                        fecha_nacimiento=%s, tipo_perfil=%s, institucion=%s
                    WHERE id_usuario = %s
                """, (nombre, apellidos, correo, telefono, direccion,
                      fecha_nacimiento, tipo_perfil, institucion, id_usuario_global))
        elif usuario_google:
            if foto and foto.filename != '':
                try:
                    # Procesar la imagen con Pillow
                    imagen = Image.open(foto)
                    print(f"Imagen cargada correctamente: {foto.filename}")
                    img_io = io.BytesIO()
                    imagen = imagen.convert('RGB')  # Asegúrate de convertirla a RGB si no lo está
                    imagen.save(img_io, 'JPEG')  # Guardarla en formato JPEG o el que prefieras
                    img_io.seek(0)
                    foto_blob = img_io.read()
                    print(f"Imagen procesada correctamente en formato BLOB")

                    cursor.execute("""
                        UPDATE Usuarios_Google
                        SET nombre=%s, apellidos=%s, correo=%s, telefono=%s, direccion=%s,
                            fecha_nacimiento=%s, tipo_perfil=%s, institucion=%s, imagen=%s
                        WHERE id_usuario_google = %s
                    """, (nombre, apellidos, correo, telefono, direccion,
                          fecha_nacimiento, tipo_perfil, institucion, foto_blob, id_usuario_global))
                except Exception as e:
                    print(f"Error al procesar la imagen: {e}")
                    return "Error al procesar la imagen."
            else:
                cursor.execute("""
                    UPDATE Usuarios_Google
                    SET nombre=%s, apellidos=%s, correo=%s, telefono=%s, direccion=%s,
                        fecha_nacimiento=%s, tipo_perfil=%s, institucion=%s
                    WHERE id_usuario_google = %s
                """, (nombre, apellidos, correo, telefono, direccion,
                      fecha_nacimiento, tipo_perfil, institucion, id_usuario_global))

        conn.commit()

    # GET (o después de POST): cargar datos actualizados
    if usuario_normal:
        cursor.execute("""
            SELECT nombre, apellidos, correo, telefono, direccion, fecha_nacimiento, 
                   tipo_perfil, institucion, foto_perfil
            FROM Usuarios WHERE id_usuario = %s
        """, (id_usuario_global,))
    elif usuario_google:
        cursor.execute("""
            SELECT nombre, apellidos, correo, telefono, direccion, fecha_nacimiento, 
                   tipo_perfil, institucion, imagen
            FROM Usuarios_Google WHERE id_usuario_google = %s
        """, (id_usuario_global,))

    user_data = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user_data:
        return redirect(url_for('login'))

    campos = [
        'nombre', 'apellidos', 'correo', 'telefono', 'direccion', 'fecha_nacimiento',
        'tipo_perfil', 'institucion', 'foto_perfil' if usuario_normal else 'imagen'
    ]
    usuario_dict = dict(zip(campos, user_data))

    imagen_blob = usuario_dict.get('foto_perfil' if usuario_normal else 'imagen')
    if imagen_blob:
        imagen_base64 = base64.b64encode(imagen_blob).decode('utf-8')
        usuario_dict['imagen_base64'] = f"data:image/jpeg;base64,{imagen_base64}"
    else:
        usuario_dict['imagen_base64'] = '/static/image/LogoAla.png'

    return render_template('editar_perfil.html', usuario=usuario_dict)


# Funcion para salir de la sesion
@app.route('/logout')
def logout():
    # Eliminar la sesión del usuario
    session.pop('user_id', None)
    session.pop('email', None)
    session.clear()
    # Redirigir al login
    return redirect(url_for('login'))

# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Funcion para el pago de paquetes
# Ruta para el pago
@app.route('/stripe_pay', methods=['POST'])
def stripe_pay():
    stripe_secret_key = app.config.get('STRIPE_SECRET_KEY', '')
    stripe.api_key = stripe_secret_key
    print("Modo de prueba de Stripe" if 'test' in stripe_secret_key else "Modo de producción de Stripe")

    data = request.json
    horas = data.get("horas")
    precio_cliente = data.get("precio")

    print(f"Datos recibidos - Horas: {horas}, Precio cliente: {precio_cliente}")

    if not horas:
        return jsonify({"error": "Falta el parámetro de horas"}), 400

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        # Buscar paquete exacto
        cursor.execute("SELECT id_paquete, descripcion, precio FROM Paquetes WHERE horas = %s", (horas,))
        paquete = cursor.fetchone()

        if not paquete:
            print(f"No se encontró paquete con {horas} horas. Buscando uno con más horas o igual.")
            cursor.execute("""
                SELECT id_paquete, descripcion, precio FROM Paquetes
                WHERE horas > %s
                ORDER BY horas ASC
                LIMIT 1
            """, (horas,))
            paquete = cursor.fetchone()

            if not paquete:
                print("No se encontró uno mayor. Buscando uno con menos horas.")
                cursor.execute("""
                    SELECT id_paquete, descripcion, precio FROM Paquetes
                    WHERE horas < %s
                    ORDER BY horas DESC
                    LIMIT 1
                """, (horas,))
                paquete = cursor.fetchone()

                if not paquete:
                    return jsonify({"error": "No se encontró ningún paquete cercano a las horas solicitadas"}), 404

                # Usar precio del paquete con menos horas
                precio_usado = float(paquete["precio"])
                print(f"Usando paquete con menos horas. Precio desde DB: {precio_usado}")
            else:
                # Usar precio del paquete con más horas
                precio_usado = float(paquete["precio"])
                print(f"Usando paquete con más horas. Precio desde DB: {precio_usado}")
        else:
            # Paquete exacto encontrado
            precio_usado = float(precio_cliente)
            print(f"Usando precio del cliente: {precio_usado}")

        descripcion = paquete["descripcion"]
        id_paquete = paquete["id_paquete"]
        precio_centavos = int(precio_usado * 100)

        # Crear la sesión de pago con Stripe
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'mxn',
                    'product_data': {
                        'name': descripcion,
                    },
                    'unit_amount': precio_centavos,
                },
                'quantity': 1
            }],
            mode='payment',
            success_url=url_for('thanks', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('paquetes', _external=True),
            metadata={
                'id_paquete': id_paquete
            }
        )

        return jsonify({
            'checkout_session_id': session['id'],
            'checkout_public_key': app.config['STRIPE_PUBLIC_KEY'],
            'id_paquete': id_paquete,
            'descripcion': descripcion,
            'precio': precio_usado
        })

    except mysql.connector.Error as db_error:
        print(f"Error en la base de datos: {db_error}")
        return jsonify({"error": f"Error en la base de datos: {str(db_error)}"}), 500

    except stripe.error.StripeError as stripe_error:
        print(f"Error de Stripe: {stripe_error}")
        return jsonify({"error": f"Error de Stripe: {str(stripe_error)}"}), 500

    except Exception as e:
        print(f"Error al generar la sesión de pago: {str(e)}")
        return jsonify({"error": f"Error al generar la sesión de pago: {str(e)}"}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Ruta para confirmar el pago y asociarlo a la reserva
@app.route('/thanks')
def thanks():
    # Variables globales de control
    global usuario_google, usuario_normal, id_usuario_global
    session_id = request.args.get('session_id')

    cursor = None
    connection = None

    if not session_id:
        return jsonify({"error": "Falta el parámetro session_id"}), 400

    try:
        session = stripe.checkout.Session.retrieve(session_id)

        if session.payment_status != 'paid':
            return jsonify({"error": "El pago no fue completado correctamente"}), 400

        # Obtener datos clave desde la sesión
        amount_total = session.get('amount_total', 0) / 100
        status = session.get('payment_status', 'Desconocido')
        customer_email = session.get('customer_email', 'No disponible')
        customer_name = session.get('customer_details', {}).get('name', 'No disponible')
        
        # Obtener id_paquete desde el metadata de Stripe (variable local, no global ni en session)
        id_paquete_str = session.get('metadata', {}).get('id_paquete')
        if not id_paquete_str:
            return jsonify({"error": "No se encontró id_paquete en el metadata"}), 400

        id_paquete = int(id_paquete_str)

        # Obtener ubicación y hora local
        ubicacion_y_hora = obtener_ubicacion_y_hora()
        fecha_pago_str = ubicacion_y_hora["fecha_local"]

        # Convertir la fecha
        try:
            fecha_pago = datetime.strptime(fecha_pago_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            fecha_pago = datetime.strptime(fecha_pago_str, "%Y-%m-%d")

        location_full = ubicacion_y_hora["ubicacion_completa"]

        # Consultar los días de caducación del paquete
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT caducacion FROM Paquetes WHERE id_paquete = %s", (id_paquete,))
        paquete_info = cursor.fetchone()

        if not paquete_info:
            return jsonify({"error": "No se encontró información de caducidad para el paquete"}), 404

        caducacion_dias = paquete_info["caducacion"]
        fecha_caducidad = fecha_pago + timedelta(days=caducacion_dias)

        # Determinar el ID de usuario según el tipo
        id_usuario = id_usuario_global
        print(f"ID Usuario: {id_usuario}")
        print(f"Usuario Google: {usuario_google}, Usuario Normal: {usuario_normal}")

        # Insertar pago en la base de datos
        if usuario_google:
            cursor.execute(""" 
                INSERT INTO Pagos (monto, fecha_pago, estado, id_paquete, id_usuario, id_usuario_google, estado_paquete, fecha_caducidad, ubicacion) 
                VALUES (%s, %s, %s, %s, NULL, %s, %s, %s, %s) 
            """, (amount_total, fecha_pago, status, id_paquete, id_usuario, "no consumido", fecha_caducidad, location_full))
        elif usuario_normal:
            cursor.execute(""" 
                INSERT INTO Pagos (monto, fecha_pago, estado, id_paquete, id_usuario, id_usuario_google, estado_paquete, fecha_caducidad, ubicacion) 
                VALUES (%s, %s, %s, %s, %s, NULL, %s, %s, %s) 
            """, (amount_total, fecha_pago, status, id_paquete, id_usuario, "no consumido", fecha_caducidad, location_full))
        else:
            print("⚠️ No se detectó tipo de usuario válido.")

        connection.commit()
        id_pago = cursor.lastrowid

        # Renderizar página de agradecimiento
        return render_template('thanks.html', 
                               customer_email=customer_email,
                               amount_total=amount_total,
                               currency='MXN',
                               status=status,
                               customer_name=customer_name,
                               payment_id=id_pago)

    except mysql.connector.Error as db_error:
        return jsonify({"error": f"Error en la base de datos: {str(db_error)}"}), 500
    except stripe.error.StripeError as stripe_error:
        return jsonify({"error": f"Error de Stripe: {str(stripe_error)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Error inesperado: {str(e)}"}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Funcion para autenticacion de google
@app.route("/verificacion_google", methods=['POST', 'GET'])
def verificacion_google():
    global state_global, usuario_google, usuario_normal
    flow = Flow.from_client_secrets_file(
        'client_secrets.json',
        scopes=["openid", "https://www.googleapis.com/auth/userinfo.email"],  # Scope actualizado
        redirect_uri='https://localhost:5000/callback'
    )
    # Generamos la URL de autorización y el estado
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    # Guardamos el estado en la variable global
    state_global = state
    usuario_google = True
    usuario_normal = False
    return redirect(authorization_url)

# Ruta de callback, donde Google redirige después de la autenticación
@app.route('/callback')
def callback():
    global nombre_usuario
    try:
        global state_global
        if not state_global:
            return 'Error: No se pudo recuperar el estado de la sesión.', 400

        flow = Flow.from_client_secrets_file(
            'client_secrets.json',
            scopes=["openid", "https://www.googleapis.com/auth/userinfo.email"],
            state=state_global,
            redirect_uri='https://localhost:5000/callback'
        )

        flow.fetch_token(authorization_response=request.url)
        credentials = flow.credentials
        user_info = obtener_informacion_usuario(credentials)  # Obtenemos los datos de Google

        if user_info:
            insertar_usuario_en_db(user_info)  # Insertar usuario en la BD si no existe

            session['user'] = {
                "id": user_info.get("sub"),
                "nombre": user_info.get("name", "Usuario de Google"),
                "email": user_info.get("email"),
                "avatar": user_info.get("picture", "static/image/default-avatar.png")
            }

            # Redirigir según el tipo de solicitud
            if request.headers.get('Accept') == 'application/json':
                print(usuario_normal)
                print(usuario_google)
                return jsonify({
                    "status": "success",
                    "message": "Bienvenido",
                    "user": "usuario google"
                })
            else:
                return redirect(url_for('home'))  
        else:
            return 'Error: No se pudo obtener la información del usuario.', 400
    except Exception as e:
        return f'Error en el callback: {str(e)}', 400

# Función para obtener la información del usuario usando el token de acceso
def obtener_informacion_usuario(credentials):
    access_token = credentials.token
    url = "https://www.googleapis.com/oauth2/v3/userinfo"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url, headers=headers)
    print(f"Respuesta de la API de Google: {response.status_code} - {response.json()}")  # Ver respuesta
    if response.status_code == 200:
        print(response)
        return response.json()  # Retorna la información del usuario (nombre, correo electrónico, etc.)
    else:
        print(f"Error al obtener la información del usuario: {response.status_code}")
        return None

# Función para insertar los datos del usuario en la base de datos si no existe
def insertar_usuario_en_db(user_info):
    global id_usuario_global  # Asegurar que usamos la variable global

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Obtener la fecha actual para el registro
        fecha_registro = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        hd = user_info.get('hd', 'No tiene hd')

        # Verificar si el usuario ya está registrado
        cursor.execute("SELECT id_usuario_google FROM Usuarios_Google WHERE correo = %s", (user_info['email'],))
        existing_user = cursor.fetchone()

        if existing_user:
            id_usuario_global = existing_user[0]  # Asignar ID si ya existe
            print(f"El usuario ya existe con ID: {id_usuario_global}")
        else:
            # Insertar el usuario si no existe
            query = """
            INSERT INTO Usuarios_Google (imagen, correo, correo_verificado, fecha_registro, dominio)
            VALUES (%s, %s, %s, %s, %s)
            """
            data = (
                user_info.get('picture', 'static/image/default-avatar.png'),
                user_info['email'], 
                user_info.get('email_verified', False),
                fecha_registro,
                hd
            )
            cursor.execute(query, data)
            conn.commit()
            
            # Obtener el ID generado por la BD
            id_usuario_global = cursor.lastrowid
            print(f"Usuario {user_info['email']} insertado en la BD con ID: {id_usuario_global}")

        return id_usuario_global  # Retornar el ID del usuario

    except mysql.connector.Error as err:
        print(f"⚠️ Error al interactuar con la BD: {err}")
        return None
    finally:
        cursor.close()
        conn.close()
# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/administrador')
def administrador():
    return render_template('administrador.html')

@app.route('/datos_dashboard', methods=['GET'])
def datos_dashboard():
    connection = get_db_connection()
    if connection is None:
        return jsonify({"success": False, "error": "No se pudo conectar a la base de datos"}), 500

    cursor = connection.cursor(dictionary=True)

    try:
        # 📌 Total de Usuarios
        cursor.execute("SELECT COUNT(*) AS total_usuarios FROM Usuarios")
        total_usuarios = cursor.fetchone()["total_usuarios"]

        cursor.execute("SELECT COUNT(*) AS total_usuarios_google FROM Usuarios_Google")
        total_usuarios_google = cursor.fetchone()["total_usuarios_google"]

        total_general_usuarios = total_usuarios + total_usuarios_google

        # 📌 Total de Pagos
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN id_usuario IS NOT NULL AND estado_paquete = 'consumido' THEN 1 ELSE 0 END) AS normales_consumidos,
                SUM(CASE WHEN id_usuario IS NOT NULL AND estado_paquete = 'no_consumido' THEN 1 ELSE 0 END) AS normales_no_consumidos,
                SUM(CASE WHEN id_usuario_google IS NOT NULL AND estado_paquete = 'consumido' THEN 1 ELSE 0 END) AS google_consumidos,
                SUM(CASE WHEN id_usuario_google IS NOT NULL AND estado_paquete = 'no_consumido' THEN 1 ELSE 0 END) AS google_no_consumidos
            FROM Pagos
        """)
        pagos_totales = cursor.fetchone()
        total_pagos = sum(pagos_totales.values())

        # 📌 Total de Reservas
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN id_usuario IS NOT NULL THEN 1 ELSE 0 END) AS normales_reservas,
                SUM(CASE WHEN id_usuario_google IS NOT NULL THEN 1 ELSE 0 END) AS google_reservas
            FROM Reservas
        """)
        reservas_totales = cursor.fetchone()
        total_reservas = reservas_totales["normales_reservas"] + reservas_totales["google_reservas"]

        # 📌 Obtener datos de Usuarios y Usuarios_Google
        cursor.execute("""
            SELECT DATE(fecha_registro) AS fecha, COUNT(*) AS total_usuarios
            FROM Usuarios
            GROUP BY DATE(fecha_registro)
            ORDER BY fecha ASC
        """)
        usuarios = cursor.fetchall()

        cursor.execute("""
            SELECT DATE(fecha_registro) AS fecha, COUNT(*) AS total_usuarios_google
            FROM Usuarios_Google
            GROUP BY DATE(fecha_registro)
            ORDER BY fecha ASC
        """)
        usuarios_google = cursor.fetchall()

        # 📌 Obtener datos de Pagos
        cursor.execute("""
            SELECT DATE(fecha_pago) AS fecha, 
                SUM(CASE WHEN id_usuario IS NOT NULL AND estado_paquete = 'consumido' THEN 1 ELSE 0 END) AS normales_consumidos,
                SUM(CASE WHEN id_usuario IS NOT NULL AND estado_paquete = 'no_consumido' THEN 1 ELSE 0 END) AS normales_no_consumidos,
                SUM(CASE WHEN id_usuario_google IS NOT NULL AND estado_paquete = 'consumido' THEN 1 ELSE 0 END) AS google_consumidos,
                SUM(CASE WHEN id_usuario_google IS NOT NULL AND estado_paquete = 'no_consumido' THEN 1 ELSE 0 END) AS google_no_consumidos
            FROM Pagos
            GROUP BY DATE(fecha_pago)
            ORDER BY fecha ASC
        """)
        pagos = cursor.fetchall()

        # 📌 Obtener datos de Reservas usando fecha_reserva y ordenadas
        cursor.execute("""
            SELECT 
                DATE(fecha_reserva) AS fecha,
                estado_reserva,
                SUM(CASE WHEN id_usuario IS NOT NULL THEN 1 ELSE 0 END) AS usuarios_normales,
                SUM(CASE WHEN id_usuario_google IS NOT NULL THEN 1 ELSE 0 END) AS usuarios_google
            FROM Reservas
            GROUP BY fecha, estado_reserva
            ORDER BY fecha ASC
        """)
        reservas = cursor.fetchall()

        # 📌 Formatear datos en JSON para el frontend
        return jsonify({
            "success": True,
            "totales": {
                "usuarios": {"total": total_general_usuarios, "normales": total_usuarios, "google": total_usuarios_google},
                "pagos": {
                    "total": total_pagos,
                    "normales_consumidos": pagos_totales["normales_consumidos"],
                    "normales_no_consumidos": pagos_totales["normales_no_consumidos"],
                    "google_consumidos": pagos_totales["google_consumidos"],
                    "google_no_consumidos": pagos_totales["google_no_consumidos"]
                },
                "reservas": {
                    "total": total_reservas,
                    "normales": reservas_totales["normales_reservas"],
                    "google": reservas_totales["google_reservas"]
                }
            },
            "usuarios": usuarios,
            "usuarios_google": usuarios_google,
            "pagos": pagos,
            "reservas": reservas
        })

    except mysql.connector.Error as e:
        return jsonify({"success": False, "error": f"Error en la base de datos: {e}"}), 500

    finally:
        cursor.close()
        connection.close()
# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Rutas temporales
@app.route('/carga', methods=['GET', 'POST'])
def carga():
    return render_template('carga.html')

@app.route('/acceso_token', methods=['GET', 'POST'])
def acceso_token():
    return render_template('acceso_token.html')

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#CRUD de la modificacion de los paquetes
def alert_message(message, redirect_url='/'):
    return f"<script>alert('{message}'); window.location.href='{redirect_url}';</script>"

@app.route('/paquetes_lista', methods=['GET'])
def paquetes_lista():
    conn = get_db_connection()
    if conn is None:
        return "Error al conectar a la base de datos.", 500

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Paquetes")
    paquetes = cursor.fetchall()
    cursor.close()
    conn.close()

    paquetes_array = [{
        "ID": paquete[0],
        "NOMBRE_PAQUETE": paquete[1],
        "DESCRIPCION": paquete[2],
        "PRECIO": float(paquete[3]),
        "MONEDA": paquete[4],
        "FECHA_CREACION": paquete[5],
        "CADUCACION": paquete[6],
        "HORAS": paquete[7]
    } for paquete in paquetes]

    return render_template('paquetes_lista.html', paquetes=paquetes_array)

@app.route('/modificar_paquete/<int:id>', methods=['POST'])
def modificar_paquete(id):
    data = request.get_json()
    nombre_paquete = data.get('nombre_paquete')
    descripcion = data.get('descripcion')
    precio = data.get('precio')
    moneda = data.get('moneda')
    caducacion = data.get('caducacion')
    horas = data.get('horas')

    # Validación de los datos
    if not all([nombre_paquete, descripcion, precio, moneda, caducacion, horas]):
        return jsonify({"success": False, "message": "Faltan datos requeridos"}), 400

    try:
        connection = get_db_connection()
        if connection is None:
            return jsonify({"success": False, "message": "No se pudo establecer conexión con la base de datos"}), 500

        cursor = connection.cursor()

        # Actualizar los datos en la base de datos
        cursor.execute('''
            UPDATE Paquetes SET
                NOMBRE_PAQUETE = %s,
                DESCRIPCION = %s,
                PRECIO = %s,
                MONEDA = %s,
                CADUCACION = %s,
                HORAS = %s
            WHERE ID_PAQUETE = %s
        ''', (nombre_paquete, descripcion, precio, moneda, caducacion, horas, id))

        connection.commit()
        connection.close()

        return jsonify({"success": True, "message": "Paquete modificado con éxito"})
    except mysql.connector.Error as e:
        return jsonify({"success": False, "message": f"Error al modificar el paquete: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"success": False, "message": f"Error inesperado: {str(e)}"}), 500

@app.route('/eliminar_paquete/<int:id>', methods=['POST'])
def eliminar_paquete(id):
    conn = get_db_connection()
    if conn is None:
        return "Error al conectar a la base de datos.", 500

    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Paquetes WHERE id_paquete = %s", (id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/insertar_paquete', methods=['GET', 'POST'])
def insertar_paquete():
    if request.method == 'POST':
        nombre = request.form.get('nombre_paquete')
        descripcion = request.form.get('descripcion')
        precio = request.form.get('precio')
        moneda = request.form.get('moneda')
        caducacion = request.form.get('caducacion')
        horas = request.form.get('horas')

        if not nombre or not descripcion or not precio or not moneda or not caducacion or not horas:
            return alert_message("Todos los campos son obligatorios.")

        conn = get_db_connection()
        if conn is None:
            return "Error al conectar a la base de datos.", 500

        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO Paquetes (nombre_paquete, descripcion, precio, moneda, caducacion, horas)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (nombre, descripcion, precio, moneda, caducacion, horas))
            conn.commit()
            conn.close()
            return alert_message("Paquete insertado correctamente.", '/paquetes_lista')
        except Exception as e:
            conn.close()
            return alert_message(f"Error al insertar el paquete: {str(e)}")

    return render_template('insertar_paquete.html')
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/tutoriales', methods=['GET','POST'])
def tutoriales():
    global id_usuario_global, usuario_normal, usuario_google

    # Redirigir a login si el usuario no está autenticado
    if not (usuario_normal or usuario_google):
        return redirect(url_for('login'))

    if not id_usuario_global:
        return redirect(url_for('login'))

    return render_template('tutoriales.html')
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Funcionar la API
if __name__ == '__main__':
   app.run(debug=True, host='0.0.0.0', ssl_context='adhoc') # El ssl es para crear un HTTPS, el adhoc es para hacerlo sin la necesidad de credenciales
