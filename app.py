import os
import math
from flask import Flask, render_template, request, redirect, url_for
from google.cloud import dialogflow_v2beta1 as dialogflow
from werkzeug import secure_filename
import chess.pgn
from stockfish import Stockfish
from matplotlib import pyplot as plt
from itertools import tee, islice, chain
app = Flask(__name__)

# Carpeta de subida
app.config['UPLOAD_FOLDER'] = './Archivos PGN'
app.config['TEMPLATES_AUTO_RELOAD'] = True

# configuración de Dialogflow
DIALOGFLOW_PROJECT_ID = 'chatbotajedrez-egub'
DIALOGFLOW_LANGUAGE_CODE = 'es'
SESSION_ID = 'session_id'

# crear una instancia de Dialogflow
session_client = dialogflow.SessionsClient()
session = session_client.session_path(DIALOGFLOW_PROJECT_ID, SESSION_ID)


nombreArchivo = "Ninguno"
graficaAnalizada = ""
pgn = None
partida = ""
puntuacion = 0
game = None
nombre_blancas = ""
nombre_negras = ""
ganador = ""
ladoGanador = ""

evaluacion = []
diferencias = []
turno = 0
posicionErrorBlancas = ""
posicionErrorNegras = ""
posicionMejorBlancas = ""
posicionMejorNegras = ""
posicionMateBlancas = ""
posicionMateNegras = ""
posicionFinal = ""

turnoErrorBlancas = 0
turnoErrorNegras = 0
turnoMejorBlancas = 0
turnoMejorNegras = 0
turnoMateBlancas = 0
turnoMateNegras = 0
turnoFinal = 0

centiErrorBlancas = 0
centiErrorNegras = 0
centiMejorBlancas = 0
centiMejorNegras = 0

centiActualErrorBlancas = 0
centiActualMejorBlancas = 0
centiActualErrorNegras = 0
centiActualMejorNegras = 0


centiMejorMovimientoErrorBlancas = 0
centiMejorMovimientoErrorNegras = 0
centiMejorMovimientoMejorBlancas = 0
centiMejorMovimientoMejorNegras = 0

moveMejorBlancas = ""
moveMejorNegras = ""
moveErrorBlancas = ""
moveErrorNegras = ""
moveMateBlancas = ""
moveMateNegras = ""

bestMoveMejorBlancas = ""
bestMoveMejorNegras = ""
bestMoveErrorBlancas = ""
bestMoveErrorNegras = ""
bestMoveMateBlancas = ""
bestMoveMateNegras = ""

stockfish = Stockfish(path="/home/ubuntu/Desktop/TFG/src/stockfish")


# Routes to Render Something
@app.route('/', methods=['POST', 'GET'])
def home():

    return render_template("home.html", nombreArchivo=nombreArchivo, partida=partida)



@app.route('/procesarMensaje', methods=['POST'])
def procesarMensaje():
    user_input = request.form['mensaje']

    # enviar la entrada del usuario a Dialogflow
    text_input = dialogflow.types.TextInput(text=user_input, language_code=DIALOGFLOW_LANGUAGE_CODE)
    query_input = dialogflow.types.QueryInput(text=text_input)
    response = session_client.detect_intent(session=session, query_input=query_input)

    # obtener la respuesta de Dialogflow
    bot_message = response.query_result.fulfillment_text

    if ("mate blancas" in bot_message):
        if (turnoMateBlancas == 0):
            bot_message = "Las blancas no han tenido oportunidad de mate a lo largo de la partida"
    elif ("mate negras" in bot_message):
        if (turnoMateNegras == 0):
            bot_message = "Las negras no han tenido oportunidad de mate a lo largo de la partida"

    respuesta = '<p><strong>Tú</strong>: ' + user_input + '</p>\n<p><strong>Chatbot</strong>: ' + bot_message + '</p>'

    return respuesta

@app.route("/upload", methods=['POST'])
def uploader():
    global pgn, nombreArchivo
    if request.method == 'POST':
        # Obtenemos el archivo del input "archivo"
        f = request.files['archivo']
        filename = secure_filename(f.filename)
        # Guardamos el archivo en el directorio "Archivos PGN"
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        # Retornamos una respuesta satisfactoria
        nombreArchivo = filename

        if ".pgn" not in nombreArchivo:
            return redirect(url_for('error'))

        pgn = open("Archivos PGN/"+filename)

    return redirect(url_for('partida'))


@app.route('/error', methods=['GET', 'POST'])
def error():

    return render_template("error.html")


@app.route('/partida', methods=['GET', 'POST'])
def partida():
    global partida, game, nombre_blancas, nombre_negras, ganador,ladoGanador

    game = chess.pgn.read_game(pgn)
    headers = game.headers
    nombre_blancas = headers.get('White')
    nombre_negras = headers.get('Black')
    resultado = headers.get('Result')

    if resultado == '1-0':
        ganador = nombre_blancas
        ladoGanador = "blancas"
    elif resultado == '0-1':
        ganador = nombre_negras
        ladoGanador = "negras"
    else:
        ganador = "Empate"
        ladoGanador = "empate"

    partida = game.mainline_moves()



    return render_template("partida.html", nombreArchivo=nombreArchivo, nombre_blancas=nombre_blancas, nombre_negras=nombre_negras, ganador=ganador, partida=partida)


@app.route('/analizada', methods=['GET', 'POST'])
def analizada():
    global partida, turno, puntuacion, graficaAnalizada

    profundidad = request.form.get('profundidad')

    if (profundidad is not None):
        stockfish.set_depth(profundidad)  # Profundidad 20 MAX
        stockfish.set_skill_level(20)  # Nivel 20 MAX
        stockfish.get_parameters()
        # stockfish.set_fen_position(game.board().fen())
        analizarPartida()

    return render_template("analizada.html", nombreArchivo=nombreArchivo, nombre_blancas=nombre_blancas, nombre_negras=nombre_negras, ganador=ganador, partida=partida, graficaAnalizada = graficaAnalizada)


@app.route('/jugada/<tipo>', methods=['GET', 'POST'])
def jugada(tipo):
    global partida, puntuacion

    if tipo == "mejorBlancas":
        posicion = posicionMejorBlancas
        turno = math.ceil(turnoMejorBlancas/2)
        lado = "Blancas"
        jugada = "Mejor jugada blancas"
        centi = centiActualMejorBlancas
        move = moveMejorBlancas
        bestMove = bestMoveMejorBlancas
        movCenti = centiMejorBlancas
        mejorCenti = centiMejorMovimientoMejorBlancas

    if tipo == "mejorNegras":
        posicion = posicionMejorNegras
        turno = math.ceil(turnoMejorNegras/2)
        lado = "Negras"
        jugada = "Mejor jugada negras"
        centi = centiActualMejorNegras
        move = moveMejorNegras
        bestMove = bestMoveMejorNegras
        movCenti = centiMejorNegras
        mejorCenti = centiMejorMovimientoMejorNegras

    if tipo == "errorBlancas":
        posicion = posicionErrorBlancas
        turno = math.ceil(turnoErrorBlancas/2)
        lado = "Blancas"
        jugada = "Mayor error blancas"
        centi = centiActualErrorBlancas
        move = moveErrorBlancas
        bestMove = bestMoveErrorBlancas
        movCenti = centiErrorBlancas
        mejorCenti = centiMejorMovimientoErrorBlancas

    if tipo == "errorNegras":
        posicion = posicionErrorNegras
        turno = math.ceil(turnoErrorNegras/2)
        lado = "Negras"
        jugada = "Mayor error negras"
        centi = centiActualErrorNegras
        move = moveErrorNegras
        bestMove = bestMoveErrorNegras
        movCenti = centiErrorNegras
        mejorCenti = centiMejorMovimientoErrorNegras

    if tipo == "posibleMateBlancas":
        posicion = posicionMateBlancas
        turno = math.ceil(turnoMateBlancas/2)
        lado = "Blancas"
        jugada = "Primer posible mate blancas"
        centi = "Mate"
        movCenti = 0
        mejorCenti = 0
        move = moveMateBlancas
        bestMove = bestMoveMateBlancas

    if tipo == "posibleMateNegras":
        posicion = posicionMateNegras
        turno = math.ceil(turnoMateNegras/2)
        lado = "Negras"
        jugada = "Primer posible mate negras"
        centi = "Mate"
        movCenti = 0
        mejorCenti = 0
        move = moveMateNegras
        bestMove = bestMoveMateNegras

    if tipo == "final":
        posicion = posicionFinal
        turno = math.ceil(turnoFinal/2)
        if (turno % 2 == 0):
            lado = "Blancas"
        else:
            lado = "Negras"
        jugada = "Final"
        centi = "Mate"
        movCenti = 0
        mejorCenti = 0
        move = ""
        bestMove = ""

    # return redirect(url_for('jugada',tipo = tipo))
    return render_template("jugada.html", nombreArchivo=nombreArchivo, nombre_blancas=nombre_blancas, nombre_negras=nombre_negras, ganador=ganador, partida=partida,graficaAnalizada=graficaAnalizada, posicion=posicion, turno=turno, centi=centi, move=move, bestMove=bestMove, movCenti=movCenti,mejorCenti=mejorCenti, lado=lado, jugada=jugada)


def analizarPartida():
    global partida, game, evaluacion, diferencias, posicionMate, turnoMate
    global posicionErrorBlancas, posicionErrorNegras, posicionMejorBlancas, posicionMejorNegras, posicionMateBlancas, posicionMateNegras, posicionFinal
    global turnoErrorBlancas, turnoErrorNegras, turnoMejorBlancas, turnoMejorNegras, turnoMateBlancas, turnoMateNegras, turnoFinal
    global centiErrorBlancas, centiErrorNegras, centiMejorBlancas, centiMejorNegras, centiActual, centiMejorMovimiento
    global moveMejorBlancas, moveMejorNegras, moveErrorBlancas, moveErrorNegras, moveMateNegras,moveMateBlancas
    global centiActualErrorBlancas, centiActualErrorNegras, centiActualMejorBlancas, centiActualMejorNegras
    global bestMoveMejorBlancas, bestMoveMejorNegras, bestMoveErrorBlancas, bestMoveErrorNegras, bestMoveMateBlancas, bestMoveMateNegras
    global centiMejorMovimientoErrorBlancas, centiMejorMovimientoErrorNegras, centiMejorMovimientoMejorBlancas, centiMejorMovimientoMejorNegras
    global graficaAnalizada

    posicionErrorBlancas = ""
    posicionErrorNegras = ""
    posicionMejorBlancas = ""
    posicionMejorNegras = ""
    posicionMateBlancas = ""
    posicionMateNegras = ""

    turnoErrorBlancas = 0
    turnoErrorNegras = 0
    turnoMejorBlancas = 0
    turnoMejorNegras = 0
    turnoMateBlancas = 0
    turnoMateNegras = 0

    centiErrorBlancas = 0
    centiErrorNegras = 0
    centiMejorBlancas = 0
    centiMejorNegras = 0

    centiActualErrorBlancas = 0
    centiActualErrorNegras = 0
    centiActualMejorBlancas = 0
    centiActualMejorNegras = 0

    centiMejorMovimientoErrorBlancas = 0
    centiMejorMovimientoErrorNegras = 0
    centiMejorMovimientoMejorBlancas = 0
    centiMejorMovimientoMejorNegras = 0

    moveMejorBlancas = ""
    moveMejorNegras = ""
    moveErrorBlancas = ""
    moveErrorNegras = ""
    moveMateNegras = ""
    moveMateBlancas = ""

    bestMoveMejorBlancas = ""
    bestMoveMejorNegras = ""
    bestMoveErrorBlancas = ""
    bestMoveErrorNegras = ""
    bestMoveMateBlancas = ""
    bestMoveMateNegras = ""

    evaluacion = []
    diferencias = []
    turnos = []
    tablero = game.board()
    stockfish.set_fen_position(tablero.fen())
    evaluacionAnterior = stockfish.get_evaluation()['value']
    turno = 1
    turnos.append(turno)
    evaluacion.append(evaluacionAnterior)
    diferencias.append(evaluacionAnterior)
    diferenciaMayor = 0


    for previos, move, next in previous_and_next(partida):

        tablero.push(move)
        stockfish.set_fen_position(tablero.fen())
        ev = stockfish.get_evaluation()

        if (ev['type'] == "cp"):
            evaluacionPosterior = ev['value']
            evaluacion.append(evaluacionPosterior)
            diferencia = evaluacionPosterior - evaluacionAnterior
            diferencias.append(diferencia)
            if abs(diferencia) > abs(diferenciaMayor):
                diferenciaMayor = diferencia
            evaluacionAnterior = evaluacionPosterior
            turnos.append(turno)

        if (ev['type'] == "mate") and (ev['value'] == -1):

            bestMove = stockfish.get_best_move()
            posicionMate = tablero.fen()
            moveMate = next
            if ((turno % 2) == 0):
                turnoMateBlancas = turno
                bestMoveMateBlancas = bestMove
                posicionMateBlancas = posicionMate
                moveMateBlancas = moveMate
            else:
                turnoMateNegras = turno
                bestMoveMateNegras = bestMove
                posicionMateNegras = posicionMate
                moveMateNegras = moveMate

        if (next is None):
            turnoFinal = turno
            posicionFinal = tablero.fen()
            
        turno += 1


    analizar_Aciertos_y_Errores()

    #Analizamos la grafica

    positivos = 0
    negativos = 0

    for valor in evaluacion:
        if valor < 0:
            negativos += 1
        else:
            positivos += 1

    umbral = (3/4) * len(evaluacion)

    if (negativos > umbral):
        graficaAnalizada = "La partida ha sido dominada por las negras y acabaron ganando las " + ladoGanador + ".\n"

    elif (positivos > umbral):
        graficaAnalizada = "La partida ha sido dominada por las blancas y acabaron ganando las " + ladoGanador + ".\n"

    else:
        graficaAnalizada = "La partida ha estado disputada y acabaron ganando las " + ladoGanador + ".\n"

    mayor_valor = max(evaluacion)
    menor_valor = min(evaluacion)
    indice_mayor = evaluacion.index(mayor_valor)
    indice_menor = evaluacion.index(menor_valor)

    puntos_relevancia = "Las blancas han alcanzado el momento de mayor ventaja (" + str(mayor_valor) +") en el turno " + str(indice_mayor) + ".\n"
    puntos_relevancia = puntos_relevancia + "Mientras que el momento de mayor ventaja de las negras fue en el turno " + str(indice_menor) + " con una ventaja de " + str(menor_valor) + ".\n"
    graficaAnalizada = graficaAnalizada + puntos_relevancia

    ultimo = None

    if (evaluacion[-1] > 0):
        for puntuacion in reversed(evaluacion):
            if puntuacion < 0:
                ultimo = puntuacion
                break

        if ultimo is None:
            ultimo_cambio = "Las negras nunca tuvieron ventaja a lo largo de la partida."
            
        else:
            turno_cambio = evaluacion.index(ultimo)
            ultimo_cambio = "A partir del turno " + str(turno_cambio) + " las blancas dominaron la ventaja hasta el final."

    else:
        for puntuacion in reversed(evaluacion):
            if puntuacion > 0:
                ultimo = puntuacion
                break

        if ultimo is None:
            ultimo_cambio = "Las blancas nunca tuvieron ventaja a lo largo de la partida."
            
        else:
            turno_cambio = evaluacion.index(ultimo)
            ultimo_cambio = "A partir del turno " + str(turno_cambio) + " las negras dominaron la ventaja hasta el final."

    graficaAnalizada = graficaAnalizada + ultimo_cambio

    plt.bar(turnos, evaluacion)
    plt.xlabel("Num Movimiento")
    plt.ylabel("Evaluación en Centipawns (+ Blancas | - Negras)")
    plt.title("Gráfica Evaluación de la Partida")
    plt.savefig("static/img/grafica.png")
    plt.close()


def analizar_Aciertos_y_Errores():

    # En evaluacion y diferencia posiciones impares corresponden a los movimientos de las blancas y los pares de las negras
    # Las diferencias positivas favorecen a las blancas y las negativas a las negras
    global posicionErrorBlancas, posicionErrorNegras, posicionMejorBlancas, posicionMejorNegras
    global turnoErrorBlancas, turnoErrorNegras, turnoMejorBlancas, turnoMejorNegras
    global centiErrorBlancas, centiErrorNegras, centiMejorBlancas, centiMejorNegras
    global centiActualErrorBlancas, centiActualErrorNegras, centiActualMejorBlancas, centiActualMejorNegras
    global centiMejorMovimientoMejorBlancas, centiMejorMovimientoErrorBlancas, centiMejorMovimientoErrorNegras, centiMejorMovimientoMejorNegras
    global moveMejorBlancas, moveMejorNegras, moveErrorBlancas, moveErrorNegras
    global bestMoveMejorBlancas, bestMoveMejorNegras, bestMoveErrorBlancas, bestMoveErrorNegras

    minJugadaNegras = diferencias[2]
    turnoMejorNegras = 2

    for indiceMejorNegras in range(2, len(diferencias), 2):

        if indiceMejorNegras == 0: #Se ignora la posicion inicial del tablero
            continue

        if diferencias[indiceMejorNegras] < minJugadaNegras:
            minJugadaNegras = diferencias[indiceMejorNegras]
            turnoMejorNegras = indiceMejorNegras
            centiMejorNegras = diferencias[indiceMejorNegras]
            centiActualMejorNegras = evaluacion[indiceMejorNegras-1]

    maxJugadaBlancas = diferencias[1]
    turnoMejorBlancas = 1

    for indiceMejorBlancas in range(1, len(diferencias), 2):

        if diferencias[indiceMejorBlancas] > maxJugadaBlancas:
            maxJugadaBlancas = diferencias[indiceMejorBlancas]
            turnoMejorBlancas = indiceMejorBlancas
            centiMejorBlancas = diferencias[indiceMejorBlancas]
            centiActualMejorBlancas = evaluacion[indiceMejorBlancas-1]

    maxErrorNegras = diferencias[2]
    turnoErrorNegras = 2
    for indiceErrorNegras in range(2, len(diferencias), 2):
        if indiceErrorNegras == 0: #Se ignora la posicion inicial del tablero
            continue

        if diferencias[indiceErrorNegras] > maxErrorNegras:
            maxErrorNegras = diferencias[indiceErrorNegras]
            turnoErrorNegras = indiceErrorNegras
            centiErrorNegras = diferencias[indiceErrorNegras]
            centiActualErrorNegras = evaluacion[indiceErrorNegras-1]

    minErrorBlancas = diferencias[1]
    turnoErrorBlancas = 1
    for indiceErrorBlancas in range(1, len(diferencias), 2):

        if diferencias[indiceErrorBlancas] < minErrorBlancas:
            minErrorBlancas = diferencias[indiceErrorBlancas]
            turnoErrorBlancas = indiceErrorBlancas
            centiErrorBlancas = diferencias[indiceErrorBlancas]
            centiActualErrorBlancas = evaluacion[indiceErrorBlancas-1]

    tablero = game.board()
    i = 1
    stockfish.set_fen_position(tablero.fen())

    for previos, move, next in previous_and_next(partida):
        tablero.push(move)

        stockfish.set_fen_position(tablero.fen())

        if i == turnoMejorBlancas-1:
            posicionMejorBlancas = tablero.fen()
            moveMejorBlancas = next
            top_move = stockfish.get_top_moves(3)
            bestMoveMejorBlancas = top_move[0]['Move']
            centiMejorMovimientoMejorBlancas = top_move[0]['Centipawn'] - centiActualMejorBlancas

        if i == turnoMejorNegras-1:
            posicionMejorNegras = tablero.fen()
            moveMejorNegras = next
            top_move = stockfish.get_top_moves(3)
            bestMoveMejorNegras = top_move[0]['Move']
            centiMejorMovimientoMejorNegras = top_move[0]['Centipawn'] - centiActualMejorNegras

        if i == turnoErrorBlancas-1:
            posicionErrorBlancas = tablero.fen()
            moveErrorBlancas = next
            top_move = stockfish.get_top_moves(3)
            bestMoveErrorBlancas = top_move[0]['Move']
            centiMejorMovimientoErrorBlancas = top_move[0]['Centipawn'] - centiActualErrorBlancas

        if i == turnoErrorNegras-1:
            posicionErrorNegras = tablero.fen()
            moveErrorNegras = next
            top_move = stockfish.get_top_moves(3)
            bestMoveErrorNegras = top_move[0]['Move']
            centiMejorMovimientoErrorNegras = top_move[0]['Centipawn'] - centiActualErrorNegras

        i += 1

    return



def previous_and_next(moves):
    previos, move, siguientes = tee(moves, 3)
    previos = chain([None], previos)
    siguientes = chain(islice(siguientes, 1, None), [None])
    return zip(previos, move, siguientes)


# Make sure this we are executing this file
if __name__ == '__main__':
    app.run(debug=True)
    app.config['TEMPLATES_AUTO_RELOAD'] = True
