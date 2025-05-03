import os
import subprocess
import string
import time
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from pywinauto import Application
from pywinauto.findwindows import find_windows, ElementNotFoundError

# =================== CONFIGURACIÓN ====================
TOKEN_VALIDO = "12345"
codigo_registro = "SLiad+BM4RAC"
usuario = "ucaribe"
contrasena = "Unicaribe2025#"
# ======================================================

# 🔒 Solicita el token antes de iniciar todo
def solicitar_token():
    # Crear ventana principal
    cerrar_workspaces_abierto()
    root = tk.Tk()
    root.title("Pantalla de Carga - Acceso al Simulador")
    root.attributes('-fullscreen', True)

    # Función de validación de token
    def acceder():
        token = token_input.get()
        if not token:  # Si el token está vacío
            messagebox.showerror("Error", "Por favor ingrese su token.")  # MessageBox de error
        else:
            # Si el token no está vacío pero es incorrecto
            if token != "123":  # Cambia "valor_correcto" por el valor real del token
                messagebox.showerror("Error", "Token incorrecto. Intente nuevamente.")  # MessageBox de error
            else:
                messagebox.showinfo("Token recibido", f"Token ingresado: {token}")  # MessageBox de éxito
                root.destroy()  # Cierra la ventana si el token es correcto

    # Función para salir del modo fullscreen
    def salir_fullscreen(event):
        root.attributes('-fullscreen', False)

    root.bind("<Escape>", salir_fullscreen)

    # Tamaño de pantalla
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Cargar y redimensionar imagen de fondo
    fondo = Image.open("Fondo1.jpg").resize((screen_width, screen_height), Image.LANCZOS)
    fondo = Image.blend(fondo, Image.new("RGB", (screen_width, screen_height), (0, 0, 0)), alpha=0.5)
    fondo_tk = ImageTk.PhotoImage(fondo)

    # Canvas con imagen de fondo
    canvas = tk.Canvas(root, width=screen_width, height=screen_height)
    canvas.pack(fill="both", expand=True)
    canvas.create_image(0, 0, image=fondo_tk, anchor="nw")

    # Contenedor centrado
    frame = tk.Frame(
        root,
        bg="#37495E",         # Color más suave y elegante
        bd=0,
        highlightthickness=2,
        highlightbackground="#ffffff",
        padx=40,             # Padding horizontal
        pady=30              # Padding vertical
    )
    frame.place(relx=0.5, rely=0.5, anchor="center")

    # Cargar y mostrar logos
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

    # Título y mensaje
    tk.Label(frame, text="Acceso al Simulador", font=("Helvetica", 20), fg="white", bg="#37495E").pack(pady=(10, 5))
    tk.Label(frame, text="Ingrese su token para continuar", font=("Helvetica", 12), fg="#DDDDDD", bg="#37495E").pack()

    # Entrada de token
    token_input = tk.Entry(frame, width=30, font=("Helvetica", 12), justify="center", relief="flat")
    token_input.pack(pady=12, ipady=6)

    # Botón de acceso
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

    # Ejecutar
    root.mainloop()

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

# === INICIO DEL PROCESO ===
solicitar_token()

# Ejecutar GUI de pantalla completa
ventana_gui = mostrar_ventana_proceso()

# Buscar y ejecutar WorkSpaces
archivo_ejecutable = "workspaces.exe"
unidades = [f"{letra}:\\" for letra in string.ascii_uppercase if os.path.exists(f"{letra}:\\")]
ruta_encontrada = next((buscar_archivo(archivo_ejecutable, unidad) for unidad in unidades if buscar_archivo(archivo_ejecutable, unidad)), None)

if ruta_encontrada:
    print(f"Ejecutable encontrado en: {ruta_encontrada}")
    subprocess.Popen([ruta_encontrada])
else:
    print("No se encontró el ejecutable workspaces.exe en ninguna unidad.")
    exit()

time.sleep(20)

try:
    app = Application(backend="uia").connect(title_re=".*Amazon WorkSpaces.*")
    dlg = app.window(title_re=".*Amazon WorkSpaces.*")
    dlg.set_focus()
    print("Ventana encontrada y en foco.")
    time.sleep(1)
    
    all_controls = dlg.descendants()
    combo_box = next((ctrl for ctrl in all_controls if ctrl.element_info.control_type == "ComboBox"), None)
    if combo_box:
        edit_controls = combo_box.descendants(control_type="Edit")
    else:
        edit_controls = []

    edit_controls += [ctrl for ctrl in all_controls if ctrl.element_info.control_type == "Edit"]

    if edit_controls:
        print("Campo de registro encontrado, ingresando código...")
        edit_controls[0].set_focus()
        edit_controls[0].set_edit_text(codigo_registro)
        time.sleep(0.5)
        edit_controls[0].type_keys("{ENTER}")
        
        time.sleep(2)
        all_controls = dlg.descendants()
        aceptar_boton = next((ctrl for ctrl in all_controls if ctrl.element_info.control_type == "Button" and "Aceptar" in ctrl.window_text()), None)
        if aceptar_boton:
            aceptar_boton.click()
            print("Botón Aceptar presionado automáticamente.")
    else:
        print("No se encontró el campo de registro.")
        exit()

    print("Esperando 20 segundos para que aparezcan los campos de usuario y contraseña...")
    time.sleep(20)

    all_controls = dlg.descendants()
    auth_container = next((ctrl for ctrl in all_controls if ctrl.element_info.control_type in ["Document", "Pane"] and "Authentication" in ctrl.window_text()), None)

    if auth_container:
        auth_controls = auth_container.descendants()
        edit_controls = [ctrl for ctrl in auth_controls if ctrl.element_info.control_type == "Edit"]
    else:
        print("No se encontró el contenedor de autenticación.")
        exit()

    if len(edit_controls) >= 2:
        print("Ingresando credenciales...")
        edit_controls[0].set_focus()
        edit_controls[0].set_edit_text(usuario)
        time.sleep(0.5)

        edit_controls[1].set_focus()
        edit_controls[1].set_edit_text(contrasena)
        time.sleep(0.5)
        edit_controls[1].type_keys("{ENTER}")
    else:
        print("No se encontraron los campos de usuario y contraseña.")

except Exception as e:
    print("Error al interactuar con la ventana:", e)

# ✅ Esperar 30 segundos antes de cerrar la ventana GUI
if ventana_gui:
    print("Esperando 30 segundos antes de cerrar la ventana GUI...")
    time.sleep(30)
    ventana_gui.destroy()
