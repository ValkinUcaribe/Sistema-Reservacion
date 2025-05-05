import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

# Función para salir del modo fullscreen
def salir_fullscreen(event):
    root.attributes('-fullscreen', False)

# Crear ventana principal
root = tk.Tk()
root.title("Cargando simulador")
root.attributes('-fullscreen', True)
root.bind("<Escape>", salir_fullscreen)

# Tamaño de pantalla
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Cargar y oscurecer imagen de fondo
fondo = Image.open("static\image\Fondo1.jpg").resize((screen_width, screen_height), Image.LANCZOS)
fondo = Image.blend(fondo, Image.new("RGB", (screen_width, screen_height), (0, 0, 0)), alpha=0.4)
fondo_tk = ImageTk.PhotoImage(fondo)

# Canvas con fondo
canvas = tk.Canvas(root, width=screen_width, height=screen_height)
canvas.pack(fill="both", expand=True)
canvas.create_image(0, 0, image=fondo_tk, anchor="nw")

# Contenedor centrado
frame = tk.Frame(
    root,
    bg="#37495E",
    bd=0,
    highlightthickness=2,
    highlightbackground="#ffffff",
    padx=40,
    pady=30
)
frame.place(relx=0.5, rely=0.5, anchor="center")

# Cargar y mostrar logos
logo_frame = tk.Frame(frame, bg="#37495E")
logo_frame.pack(pady=(0, 10))

logo1_img = Image.open("static\image\LogoValkin.png").resize((160, 50), Image.LANCZOS)
logo1_tk = ImageTk.PhotoImage(logo1_img)
tk.Label(logo_frame, image=logo1_tk, bg="#37495E").pack()

logo2_img = Image.open("static\image\LogoValkinLines.png").resize((300, 30), Image.LANCZOS)
logo2_tk = ImageTk.PhotoImage(logo2_img)
tk.Label(logo_frame, image=logo2_tk, bg="#37495E").pack(pady=(5, 0))

# Mensajes de carga
tk.Label(frame, text="Accediendo al Simulador", font=("Helvetica", 16, "bold"), fg="white", bg="#37495E").pack(pady=(10, 5))
tk.Label(frame, text="Espere mientras carga...", font=("Helvetica", 12), fg="#DDDDDD", bg="#37495E").pack(pady=(0, 10))

# Barra de progreso
progress = ttk.Progressbar(frame, mode='indeterminate', length=200)
progress.pack(pady=10)
progress.start(10)  # Comienza la animación

# Ejecutar la ventana
root.mainloop()