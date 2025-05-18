from flask import Flask, render_template, request, redirect, url_for
import numpy as np
import matplotlib.pyplot as plt
import os

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            titulo = request.form['titulo']
            nombre_y = request.form['nombre_y']
            nombre_x = request.form['nombre_x']
            valores_y = list(map(float, request.form['valores_y'].split(',')))
            valores_x = list(map(float, request.form['valores_x'].split(',')))
            grado = int(request.form['grado'])

            if len(valores_x) != len(valores_y):
                return "Error: El número de valores en X y Y debe ser igual."

            # Ajuste por mínimos cuadrados
            coef = np.polyfit(valores_x, valores_y, grado)
            polinomio = np.poly1d(coef)
            valores_ajuste = polinomio(valores_x)

            # Calcular R^2
            ss_res = np.sum((valores_y - valores_ajuste) ** 2)
            ss_tot = np.sum((valores_y - np.mean(valores_y)) ** 2)
            r2 = 1 - (ss_res / ss_tot)

            # Graficar
            plt.figure(figsize=(10,5))

            # Subplot 1: solo puntos
            plt.subplot(1,2,1)
            plt.scatter(valores_x, valores_y, color='blue', label='Datos')
            plt.xlabel(nombre_x)
            plt.ylabel(nombre_y)
            plt.title(f"{titulo} - Solo puntos")
            plt.grid(True)

            # Subplot 2: ajuste
            plt.subplot(1,2,2)
            plt.scatter(valores_x, valores_y, color='blue', label='Datos')
            x_vals = np.linspace(min(valores_x), max(valores_x), 500)
            y_vals = polinomio(x_vals)
            plt.plot(x_vals, y_vals, color='red', label='Ajuste')
            plt.xlabel(nombre_x)
            plt.ylabel(nombre_y)
            plt.title(f"{titulo} - Ajuste grado {grado}
R² = {r2:.4f}
{polinomio}")
            plt.legend()
            plt.grid(True)

            # Guardar imagen
            ruta = os.path.join('static', 'grafico.png')
            plt.tight_layout()
            plt.savefig(ruta)
            plt.close()

            return render_template('index.html', imagen=ruta)

        except Exception as e:
            return f"Ocurrió un error: {e}"

    return render_template('index.html', imagen=None)

if __name__ == '__main__':
    app.run(debug=True)
