# Importando Flask y algunos paquetes del mismo
from flask import Flask, render_template, request, redirect, url_for, jsonify
import random
import datetime
from confiDB import *  # Importando conexión BD
import matplotlib.pyplot as plt
import io
import base64

# Declarando el nombre de la aplicación e inicializando - crear la aplicación Flask
app = Flask(__name__)
application = app

# Función para generar el gráfico
def generar_grafico(respuestas_evaluadas):
    # Definir los estilos de aprendizaje y las preguntas asociadas a cada uno
    estilos = {
        'Activo': [3, 5, 7, 9, 13, 20, 25, 26, 27, 35, 37, 41, 43, 46, 48, 51, 61, 67, 74, 75, 77],
        'Reflexivo': [10, 16, 18, 19, 28, 31, 31, 34, 36, 39, 42, 44, 49, 55, 58, 63, 65, 69, 70, 79],
        'Teórico': [2, 4, 6, 11, 15, 17, 21, 23, 25, 29, 33, 45, 50, 54, 60, 64, 66, 71, 78, 80],
        'Pragmático': [1, 8, 12, 14, 22, 30, 38, 40, 47, 52, 53, 56, 57, 59, 62, 68, 72, 73, 76]
    }

    categorias = ['Activo', 'Teórico', 'Reflexivo', 'Pragmático']

    # Sumar las respuestas evaluadas para cada estilo de aprendizaje
    valores = []
    for estilo, preguntas in estilos.items():
        suma = sum(respuestas_evaluadas.get(pregunta, 0) for pregunta in preguntas)
        valores.append(suma)

    # Crear el gráfico en un plano cartesiano
    plt.figure(figsize=(8, 6))
    plt.bar(categorias, valores)
    plt.title('Gráfico de Estilos de Aprendizaje')
    plt.xlabel('Estilos de Aprendizaje')
    plt.ylabel('Cantidad de Respuestas')
    plt.grid(True)

    # Convertir el gráfico a una imagen codificada en base64
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)
    img_string = base64.b64encode(img_buffer.read()).decode('utf-8')
    plt.close()

    # Formar el enlace HTML para mostrar la imagen en la plantilla
    img_html = f'<img src="data:image/png;base64,{img_string}" alt="Gráfico de Estilos de Aprendizaje">'
    return img_html

# Creando mi Decorador para el Home 
@app.route('/', methods=['GET', 'POST'])
def inicio():
    conexion_MySQLdb = connectionBD()  # Hago instancia a mi conexión desde la función
    mycursor = conexion_MySQLdb.cursor(dictionary=True)
    querySQL = "SELECT * FROM preguntas ORDER BY id ASC"
    mycursor.execute(querySQL)
    dataPreguntas = mycursor.fetchall()  # Obtener todos los registros
    totalPreguntas = len(dataPreguntas)  # Total de preguntas
    mycursor.close()  # cerrando conexion SQL
    conexion_MySQLdb.close()  # cerrando conexion de la BD

    # Creando un diccionario de posibles respuestas
    arrayRespuestas = {'SI': 'SI', 'NO': 'NO', 'Tal_vez': 'T'}
    codigo = random.randrange(100, 1000)

    return render_template('public/index.html', Preguntas=dataPreguntas, dataRespuesta=arrayRespuestas,
                           dataTotalPreguntas=totalPreguntas, codigoBD=codigo)

@app.route('/guardar-encuesta', methods=['POST'])
def savedEncuesta():
    if request.method == 'POST':
        data = request.form
        observacion = request.form['observacion']
        codigo = request.form['codigo']
        created = datetime.datetime.now()
        resultadoInsert = 0
        position = 0

        for clave, valor in data.items():
            position += 1
            if position <= 80:
                conexion_MySQLdb = connectionBD()
                mycursor = conexion_MySQLdb.cursor(dictionary=True)
                
                sql = "INSERT INTO respuestas_encuesta (id_pregunta, respuesta, codigo, observacion, created) VALUES (%s, %s, %s, %s, %s)"
                val = (position, valor, codigo, observacion, created)
                mycursor.execute(sql, val)
                conexion_MySQLdb.commit()
                resultadoInsert = mycursor.rowcount
                
                mycursor.close()
                conexion_MySQLdb.close()

        return jsonify(res=["respuesta", resultadoInsert])

    return render_template('public/index.html')

# Información de encuesta por código
@app.route('/<codigo>', methods=['GET', 'POST'])
def encuesta(codigo):
    conexion_MySQLdb = connectionBD()  # Hago instancia a mi conexión desde la función
    mycursor = conexion_MySQLdb.cursor(dictionary=True)
    mycursor.execute(
        "SELECT p.id, p.pregunta, r.respuesta, r.codigo, r.observacion, r.created FROM preguntas AS p INNER JOIN respuestas_encuesta AS r ON p.id = r.id_pregunta AND p.estatus='1' AND r.codigo=%s", 
        (codigo,))
    inforEncuesta = mycursor.fetchall()
    conexion_MySQLdb.close()  # cerrando conexion de la BD

    # Recopilar datos de respuestas para el gráfico
    respuestas_evaluadas = {}
    for respuesta in inforEncuesta:
        pregunta_id = respuesta['id']
        valor_respuesta = 1 if respuesta['respuesta'] == 'SI' else 0
        respuestas_evaluadas[pregunta_id] = valor_respuesta

    # Generar el gráfico y obtener el código HTML
    grafico_html = generar_grafico(respuestas_evaluadas)

    # Renderizar la plantilla y pasar el gráfico a la plantilla
    return render_template('public/listaEncuesta.html', data=inforEncuesta, grafico=grafico_html)

# Redireccionando cuando la página no existe
@app.errorhandler(404)
def not_found(error):
    return redirect(url_for('inicio'))

if __name__ == "__main__":
    app.run(debug=True, port=8005)
