from flask import Flask, render_template, request
import numpy as np
import matplotlib.pyplot as plt
import os
import uuid
import docx  # Se añadió para leer archivos .docx

app = Flask(__name__)

# Lista global para guardar múltiples gráficas para unificación posterior
todas_las_graficas = []

# NUEVO: función para encontrar automáticamente el mejor ajuste (grado 1 a 3)
def mejor_ajuste(x, y):
    mejor_r2 = -np.inf
    mejor_grado = 1
    mejor_polinomio = None
    for grado in range(1, 4):
        coef = np.polyfit(x, y, grado)
        pol = np.poly1d(coef)
        y_fit = pol(x)
        ss_res = np.sum((y - y_fit) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r2 = 1 - (ss_res / ss_tot)
        if r2 > mejor_r2:
            mejor_r2 = r2
            mejor_grado = grado
            mejor_polinomio = pol
    return mejor_grado, mejor_polinomio, mejor_r2

# NUEVO: función para leer tanto archivos .txt como .docx
def leer_datos_archivo(archivo):
    contenido = ""
    if archivo.filename.endswith('.txt') or archivo.filename.endswith('.csv'):
        contenido = archivo.read().decode('utf-8')
    elif archivo.filename.endswith('.docx'):
        doc = docx.Document(archivo)
        contenido = "\n".join([p.text for p in doc.paragraphs])
    else:
        raise ValueError("Tipo de archivo no soportado")

    lineas = [line.strip() for line in contenido.splitlines() if line.strip()]
    x = list(map(float, lineas[0].split(',')))
    y = list(map(float, lineas[1].split(',')))
    return x, y

@app.route('/', methods=['GET', 'POST'])
def index():
    global todas_las_graficas
    imagen_unificada = None

    if request.method == 'POST':
        try:
            accion = request.form.get('accion')

            if accion == 'unificar':
                # NUEVO: unifica varias curvas previamente graficadas
                if not todas_las_graficas:
                    return render_template('index.html', imagen=None, mensaje="No hay gráficas para unificar.")

                plt.figure()
                for curva in todas_las_graficas:
                    x_vals = np.linspace(min(curva['x']), max(curva['x']), 500)
                    y_vals = curva['polinomio'](x_vals)
                    plt.plot(x_vals, y_vals, label=f"{curva['titulo']} (Grado {curva['grado']}, R²={curva['r2']:.3f})")
                plt.xlabel(todas_las_graficas[0]['nombre_x'])
                plt.ylabel(todas_las_graficas[0]['nombre_y'])
                plt.title("Comparación de Ajustes")
                plt.legend()
                plt.grid(True)
                nombre = f"static/unificado_{uuid.uuid4().hex}.png"
                plt.savefig(nombre)
                plt.close()
                imagen_unificada = nombre
                return render_template('index.html', imagen=imagen_unificada)

            # DATOS BÁSICOS
            titulo = request.form['titulo']
            nombre_y = request.form['nombre_y']
            nombre_x = request.form['nombre_x']
            metodo = request.form['metodo']

            # NUEVO: opción para subir archivo o ingresar datos manualmente
            if metodo == 'archivo':
                archivo = request.files['archivo']
                valores_x, valores_y = leer_datos_archivo(archivo)
            else:
                valores_y = list(map(float, request.form['valores_y'].split(',')))
                valores_x = list(map(float, request.form['valores_x'].split(',')))

            if len(valores_x) != len(valores_y):
                return render_template('index.html', imagen=None, mensaje="El número de valores X e Y debe coincidir.")

            # NUEVO: ajuste automático si el usuario lo pide
            if request.form['grado'] == 'auto':
                grado, polinomio, r2 = mejor_ajuste(np.array(valores_x), np.array(valores_y))
            else:
                grado = int(request.form['grado'])
                coef = np.polyfit(valores_x, valores_y, grado)
                polinomio = np.poly1d(coef)
                valores_ajuste = polinomio(valores_x)
                ss_res = np.sum((np.array(valores_y) - valores_ajuste) ** 2)
                ss_tot = np.sum((np.array(valores_y) - np.mean(valores_y)) ** 2)
                r2 = 1 - (ss_res / ss_tot)

            # GRAFICAR
            plt.figure(figsize=(10,5))

            plt.subplot(1,2,1)
            plt.scatter(valores_x, valores_y, color='blue')
            plt.xlabel(nombre_x)
            plt.ylabel(nombre_y)
            plt.title(f"{titulo} - Solo puntos")
            plt.grid(True)

            plt.subplot(1,2,2)
            plt.scatter(valores_x, valores_y, color='blue')
            x_vals = np.linspace(min(valores_x), max(valores_x), 500)
            y_vals = polinomio(x_vals)
            plt.plot(x_vals, y_vals, color='red')
            plt.xlabel(nombre_x)
            plt.ylabel(nombre_y)
            plt.title(f"{titulo}\nGrado {grado}, R²={r2:.4f}\n{polinomio}")
            plt.grid(True)

            nombre_imagen = f"static/grafico_{uuid.uuid4().hex}.png"
            plt.tight_layout()
            plt.savefig(nombre_imagen)
            plt.close()

            # NUEVO: guardamos esta curva para posible unificación
            todas_las_graficas.append({
                'titulo': titulo,
                'grado': grado,
                'polinomio': polinomio,
                'r2': r2,
                'x': valores_x,
                'y': valores_y,
                'nombre_x': nombre_x,
                'nombre_y': nombre_y
            })

            return render_template('index.html', imagen=nombre_imagen)

        except Exception as e:
            return render_template('index.html', imagen=None, mensaje=f"Ocurrió un error: {e}")

    return render_template('index.html', imagen=None)

#  Esta parte es la modificación necesaria para Render 
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
