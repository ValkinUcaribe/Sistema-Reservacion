import subprocess
import string
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from pywinauto import Application
from pywinauto.findwindows import find_windows, ElementNotFoundError
import mysql.connector
from dotenv import load_dotenv
import os
from cryptography.fernet import Fernet 
import time
import requests
from datetime import datetime
import pytz

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos
DB_CONFIG = {
    "host": "brcwfojao80ca2qicg6w-mysql.services.clever-cloud.com",
    "port": 3306,
    "user": "usksfpvscyvgzgfk",
    "password": "TlLuVntGUsMh4X8sp3hv" ,
    "database": "brcwfojao80ca2qicg6w",
    }

# Clave Fernet desde variable de entorno
CLAVE_FERNET = "1ZvrSOtnYH91WiFRav2vn2yy50waFgvcisNBafODeMk="
print(CLAVE_FERNET)

# =================== CONFIGURACIÓN ====================
CREDENCIALES_POR_MAQUINA = {
    "1": {"usuario": "ucaribe", "contrasena": "Unicaribe2025#", "codigo_registro": "SLiad+BM4RAC"},
    "2": {"usuario": "ucaribe", "contrasena": "Unicaribe2025#", "codigo_registro": "SLiad+BM4RAx"},
    "3": {"usuario": "ucaribe", "contrasena": "Unicaribe2025#", "codigo_registro": "SLiad+BM4RAz"},
}
# ======================================================
# Función para obtener la fecha y hora local basándose en la IP pública
def obtener_ubicacion_y_hora():
    try:
        response = requests.get('https://ipinfo.io')
        location = response.json()

        timezone = location.get("timezone", "UTC")  # Default a UTC si no hay zona horaria
        local_tz = pytz.timezone(timezone)
        local_time = datetime.now(local_tz)

        return {
            "fecha_hora_local": local_time
        }
    except Exception as e:
        print("Error al obtener la hora local:", e)
        # Como fallback, usar UTC
        return {
            "fecha_hora_local": datetime.utcnow()
        }

# Función para insertar una nueva sesión
def insertar_sesion(duracion_usuario, maquina_asignada, id_reserva):
    print(duracion_usuario,maquina_asignada, id_reserva)
    datos_hora = obtener_ubicacion_y_hora()
    fecha_uso = datos_hora["fecha_hora_local"]
    estado_sesion = "activo"  # Valor fijo

    conn = get_db_connection()
    if not conn:
        print("No se pudo establecer conexión con la base de datos.")
        return

    try:
        cursor = conn.cursor()
        sql = """
            INSERT INTO Sesiones (
                duracion_usuario,
                maquina_asignada,
                id_reserva,
                fecha_uso,
                Estado_Sesion
            )
            VALUES (%s, %s, %s, %s, %s)
        """
        valores = (duracion_usuario, maquina_asignada, id_reserva, fecha_uso, estado_sesion)
        cursor.execute(sql, valores)
        conn.commit()
        print(f"✅ Sesión insertada con ID: {cursor.lastrowid}")
    except mysql.connector.Error as err:
        print("❌ Error al insertar sesión:", err)
    finally:
        cursor.close()
        conn.close()

# 🔒 Solicita el token antes de iniciar todo
def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as e:
        print("Error al conectar a la base de datos:", e)
        return None

def solicitar_token():
    resultado = {"id_reserva": None, "maquina": None, "duracion": None}
    def on_close():
        # Aquí puedes cancelar cualquier proceso antes de salir
        print("El usuario cerró la ventana. Cancelando proceso...")
        root.destroy()
        exit()  # Termina la aplicación completamente (opcional)
    
    cerrar_workspaces_abierto()
    root = tk.Tk()
    root.title("Pantalla de Carga - Acceso al Simulador")
    root.attributes('-fullscreen', True)


    def acceder():
        token = token_input.get()
        if not token:
            messagebox.showerror("Error", "Por favor ingrese su token.")
            return

        try:
            fernet = Fernet(CLAVE_FERNET.encode())
            mensaje_desencriptado = fernet.decrypt(token.encode()).decode()

            partes = mensaje_desencriptado.split('-')
            datos = {
                k.strip(): v.strip()
                for parte in partes if ':' in parte
                for k, v in [parte.split(':', 1)]
            }

            id_reserva = datos.get('Reserva')
            maquina = datos.get('Maquina')
            duracion = datos.get('Duración')

            if not id_reserva:
                messagebox.showerror("Error", "El token no contiene ID de reserva.")
                return

            credenciales = CREDENCIALES_POR_MAQUINA.get(maquina)
            if not credenciales:
                messagebox.showerror("Error", f"No se encontraron credenciales para la máquina {maquina}")
                return

            global usuario, contrasena, codigo_registro
            usuario = credenciales["usuario"]
            contrasena = credenciales["contrasena"]
            codigo_registro = credenciales["codigo_registro"]

            conn = get_db_connection()
            if conn is None:
                messagebox.showerror("Error", "No se pudo conectar a la base de datos.")
                return

            cursor = conn.cursor()
            cursor.execute("SELECT estado_reserva FROM Reservas WHERE id_reserva = %s", (id_reserva,))
            resultado_sql = cursor.fetchone()
            conn.close()

            if resultado_sql is None:
                messagebox.showerror("Error", f"No se encontró la reserva con ID {id_reserva}")
            elif resultado_sql[0].lower() != "activo":
                messagebox.showerror("Error", f"La reserva con ID {id_reserva} no está activa (estado: {resultado_sql[0]})")
            else:
                resultado["id_reserva"] = id_reserva
                resultado["maquina"] = maquina
                resultado["duracion"] = duracion
                messagebox.showinfo("Acceso concedido", f"Reserva válida: {id_reserva}")
                root.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"Token inválido o error al validar: {e}")

    def salir_fullscreen(event):
        root.attributes('-fullscreen', False)
        root.protocol("WM_DELETE_WINDOW", on_close)

    root.bind("<Escape>", salir_fullscreen)
    root.protocol("WM_DELETE_WINDOW", on_close)

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    fondo = Image.open("Fondo1.jpg").resize((screen_width, screen_height), Image.LANCZOS)
    fondo = Image.blend(fondo, Image.new("RGB", (screen_width, screen_height), (0, 0, 0)), alpha=0.5)
    fondo_tk = ImageTk.PhotoImage(fondo)

    canvas = tk.Canvas(root, width=screen_width, height=screen_height)
    canvas.pack(fill="both", expand=True)
    canvas.create_image(0, 0, image=fondo_tk, anchor="nw")

    frame = tk.Frame(root, bg="#37495E", bd=0, highlightthickness=2, highlightbackground="#ffffff", padx=40, pady=30)
    frame.place(relx=0.5, rely=0.5, anchor="center")

    logo_frame = tk.Frame(frame, bg="#37495E")
    logo_frame.pack(pady=(0, 10))

    logo1_img = Image.open("LogoValkin.png").resize((160, 50), Image.LANCZOS)
    logo1_tk = ImageTk.PhotoImage(logo1_img)
    logo1 = tk.Label(logo_frame, image=logo1_tk, bg="#37495E")
    logo1.pack()

    logo2_img = Image.open("Logo V1_1.jpg").resize((300, 30), Image.LANCZOS)
    logo2_tk = ImageTk.PhotoImage(logo2_img)
    logo2 = tk.Label(logo_frame, image=logo2_tk, bg="#37495E")
    logo2.pack(pady=(5, 0))

    tk.Label(frame, text="Acceso al Simulador", font=("Helvetica", 20), fg="white", bg="#37495E").pack(pady=(10, 5))
    tk.Label(frame, text="Ingrese su token para continuar", font=("Helvetica", 12), fg="#DDDDDD", bg="#37495E").pack()

    token_input = tk.Entry(frame, width=30, font=("Helvetica", 12), justify="center", relief="flat")
    token_input.pack(pady=12, ipady=6)

    tk.Button(
        frame,
        text="Acceder",
        font=("Helvetica", 12),
        bg="#4CAF50",
        fg="white",
        width=15,
        relief="flat",
        activebackground="#45a049",
        cursor="hand2",
        command=acceder
    ).pack(pady=(5, 10))

    root.mainloop()
    return resultado["id_reserva"], resultado["maquina"], resultado["duracion"]

# 🧹 Cierra instancias de WorkSpaces abiertas antes de continuar
def cerrar_workspaces_abierto():
    try:
        windows = find_windows(title_re=".*WorkSpaces.*", backend="uia")
        for win in windows:
            app = Application(backend="uia").connect(handle=win)
            window = app.window(handle=win)
            print("🔻 Cerrando instancia anterior de WorkSpaces...")
            window.close()
            time.sleep(1)
    except ElementNotFoundError:
        print("✅ No hay instancias abiertas de WorkSpaces.")
    except Exception as e:
        print("⚠️ Error al cerrar ventanas existentes:", e)

# 🖼️ Muestra ventana de GUI pantalla completa mientras corre el proceso
def mostrar_ventana_proceso():
    ventana = tk.Tk()
    ventana.attributes("-fullscreen", True)
    ventana.attributes("-topmost", True)
    ventana.configure(bg="black")
    label = tk.Label(ventana, text="🔒 Iniciando sesión en WorkSpaces...", fg="white", bg="black", font=("Helvetica", 24))
    label.pack(expand=True)
    ventana.update()
    return ventana

# 🔍 Buscar workspaces.exe en todas las unidades
def buscar_archivo(nombre_archivo, ruta_inicio):
    for root, dirs, files in os.walk(ruta_inicio, topdown=True):
        dirs[:] = [d for d in dirs if d not in ["Windows", "$Recycle.Bin", "System Volume Information"]]
        if any(nombre_archivo.lower() == f.lower() for f in files):
            return os.path.join(root, nombre_archivo)
    return None

def iniciar_sesion_reserva(id_reserva, maquina_asignada, duracion_usuario, intento=1, max_intentos=5):
    print(f"Intento #{intento} de iniciar sesión en WorkSpaces...")

    if intento > max_intentos:
        print("❌ Número máximo de intentos alcanzado. Abortando proceso.")
        return

    try:
        # === INICIO DEL PROCESO ===
        ventana_gui = mostrar_ventana_proceso()  # GUI pantalla completa

        # Buscar y ejecutar WorkSpaces
        archivo_ejecutable = "workspaces.exe"
        unidades = [f"{letra}:\\" for letra in string.ascii_uppercase if os.path.exists(f"{letra}:\\")]
        ruta_encontrada = next((buscar_archivo(archivo_ejecutable, unidad) for unidad in unidades if buscar_archivo(archivo_ejecutable, unidad)), None)

        if not ruta_encontrada:
            print("❌ No se encontró el ejecutable workspaces.exe en ninguna unidad.")
            ventana_gui.destroy()
            return iniciar_sesion_reserva(id_reserva, maquina_asignada, duracion_usuario, intento + 1)

        print(f"✅ Ejecutable encontrado en: {ruta_encontrada}")
        subprocess.Popen([ruta_encontrada])
        time.sleep(20)

        # Conectarse a la ventana
        app = Application(backend="uia").connect(title_re=".*Amazon WorkSpaces.*")
        dlg = app.window(title_re=".*Amazon WorkSpaces.*")
        dlg.set_focus()
        print("✅ Ventana encontrada y en foco.")

        # Buscar campo de código de registro
        all_controls = dlg.descendants()
        combo_box = next((ctrl for ctrl in all_controls if ctrl.element_info.control_type == "ComboBox"), None)
        edit_controls = combo_box.descendants(control_type="Edit") if combo_box else []
        edit_controls += [ctrl for ctrl in all_controls if ctrl.element_info.control_type == "Edit"]

        if not edit_controls:
            raise Exception("No se encontró el campo de código de registro.")

        print("✅ Ingresando código de registro...")
        edit_controls[0].set_focus()
        edit_controls[0].set_edit_text(codigo_registro)
        time.sleep(0.5)
        edit_controls[0].type_keys("{ENTER}")
        time.sleep(2)

        # Presionar botón "Aceptar" si aparece
        all_controls = dlg.descendants()
        aceptar_boton = next((ctrl for ctrl in all_controls if ctrl.element_info.control_type == "Button" and "Aceptar" in ctrl.window_text()), None)
        if aceptar_boton:
            aceptar_boton.click()
            print("✅ Botón Aceptar presionado automáticamente.")

        print("⌛ Esperando campos de autenticación...")
        time.sleep(20)
        all_controls = dlg.descendants()
        auth_container = next((ctrl for ctrl in all_controls if ctrl.element_info.control_type in ["Document", "Pane"] and "Authentication" in ctrl.window_text()), None)
        if not auth_container:
            raise Exception("No se encontró el contenedor de autenticación.")

        auth_controls = auth_container.descendants()
        edit_controls = [ctrl for ctrl in auth_controls if ctrl.element_info.control_type == "Edit"]
        if len(edit_controls) < 2:
            raise Exception("No se encontraron campos de usuario y contraseña.")

        print("✅ Ingresando credenciales...")
        edit_controls[0].set_focus()
        edit_controls[0].set_edit_text(usuario)
        time.sleep(0.5)
        edit_controls[1].set_focus()
        edit_controls[1].set_edit_text(contrasena)
        time.sleep(0.5)
        edit_controls[1].type_keys("{ENTER}")

        # Si llegamos aquí, el proceso fue exitoso
        insertar_sesion(duracion_usuario, maquina_asignada, id_reserva)
        print("✅ Sesión insertada correctamente.")

        print("⌛ Esperando 30 segundos antes de cerrar GUI...")
        time.sleep(30)
        if ventana_gui:
            ventana_gui.destroy()
        print("✅ GUI cerrada. Proceso finalizado.")

    except Exception as e:
        print(f"❌ Error durante el proceso: {e}")
        if ventana_gui:
            ventana_gui.destroy()
        return iniciar_sesion_reserva(id_reserva, maquina_asignada, duracion_usuario, intento + 1)

def iniciar_proceso_workspaces():

    id_reserva, maquina_asignada, duracion_usuario = solicitar_token()

    iniciar_sesion_reserva(id_reserva, maquina_asignada, duracion_usuario)

if __name__ == "__main__":
    iniciar_proceso_workspaces()
