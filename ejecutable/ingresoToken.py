import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

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



# Función para salir del modo fullscreen
def salir_fullscreen(event):
    root.attributes('-fullscreen', False)

# Crear ventana principal
root = tk.Tk()
root.title("Pantalla de Carga - Acceso al Simulador")
root.attributes('-fullscreen', True)
root.bind("<Escape>", salir_fullscreen)

# Tamaño de pantalla
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Cargar y redimensionar imagen de fondo
fondo = Image.open("static\image\Fondo1.jpg").resize((screen_width, screen_height), Image.LANCZOS)
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

logo1_img = Image.open("static\image\LogoValkin.png").resize((160, 50), Image.LANCZOS)
logo1_tk = ImageTk.PhotoImage(logo1_img)
logo1 = tk.Label(logo_frame, image=logo1_tk, bg="#37495E")
logo1.pack()

logo2_img = Image.open("static\image\LogoValkinLines.png").resize((300, 30), Image.LANCZOS)
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
