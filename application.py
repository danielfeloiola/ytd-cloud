# IMPORT STATEMENTS (DUH!)
import csv
import os
from collections import Counter
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from flask_socketio import SocketIO, emit
from helpers import apology, login_required
from api import search, query_search


# configuracoes da API
MAX_RESULTS = 5
DEVELOPER_KEY = ""


# Configura a application
app = Flask(__name__)

# socketio
socketio = SocketIO(app)

# Templates auto-reload
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configura a session
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route("/", methods=["GET", "POST"])
def index():
    """
    GET: Mostra a pagina inicial
    POST: Nao ha post
    """

    return render_template("index.html")


@app.route("/navegar", methods=["GET", "POST"])
def navegar():
    """
    GET: Mostra a pagina com o formulario
    POST: preforma a busca na API e mostra os resultados
    """

    # GET request
    if request.method == "GET":
        return render_template("navegar.html")

    # POST request
    elif request.method == "POST":

        # pega os dados da pagina
        query = request.form.get("query")
        seed = request.form.get("seed-mode")

        # determina se e necessaria uma busca por relacionados ou por termo
        if request.form.get("seed-mode") == True:
            videos = search('related', query)
        else:
            videos = search('query', query)

        # render the page
        return render_template("results.html", videos=videos)


@app.route("/coletar", methods=["GET", "POST"])
def coletar():
    """
    GET: Mostra a pagina com formulario para a coleta
    POST: preforma a busca na API e mostra os resultados

    O prceso é o mesmo da navegacao, mas e possivel fazer em diferentes
    niveis de profundidade:
    nivel 1: apenas resultados de uma busca.
    nivel 2: resultados de busca e suas recomendacoes
    nivel 3: resultados de busca, recomendacoes e recomendacoes subsequentes
    """

    # GET request
    if request.method == "GET":
        return render_template("coletar.html")

    # POST request
    elif request.method == "POST":

        # pega os dados da pagina
        query = request.form.get("query")
        seed = request.form.get("seed-mode")
        profundidade = request.form.get("profundidade")

        # lista final a ser retornada
        final_video_list = []

        # se nao for introduzido um termo ou video_id - retorna um erro
        if query == '':
            # caso a profundidade nao seja informada
            return render_template("coletar.html", msg="verifique o termo buscado")

        # varia de acordo com a profundidade
        if profundidade == '1':

            if seed == True:

                videos = search('related', query)
                final_video_list += videos

            elif seed == None:

                videos = search('query', query)
                final_video_list += videos
                query_search(query)

        elif profundidade == '2':

            # Faz a busca e coloca os resultados na lista
            if seed == True:
                # level 1
                videos = search('related', query)
                final_video_list += videos

                # itera por cada resultado e faz uma busca de relacionados para cada
                for video in videos:
                    # level 2
                    videos2 = search('related', video[0])
                    final_video_list += videos2

            elif seed == None:
                # level 1
                videos = search('query', query)
                final_video_list += videos
                query_search(query)

                # itera por cada resultado e faz uma busca de relacionados para cada
                for video in videos:
                    # level 2
                    videos2 = search('related', video[0])
                    final_video_list += videos2


        elif profundidade == '3':

            level_2 = []

            # Faz a busca e coloca os resultados na lista
            if seed == True:
                # level 1
                videos = search('related', query)
                final_video_list += videos

                # itera por cada resultado e faz uma busca de relacionados para cada
                for video in videos:
                    # level 2
                    videos2 = search('related', video[0])
                    final_video_list += videos2
                    level_2 += videos2

                    # itera por cada resultado e faz uma busca de relacionados para
                    # cada um mais uma vez
                    for vd in level_2:
                        # level 3
                        videos3 = search('related', vd[0])
                        final_video_list += videos3

            elif seed == None:
                # level 1
                videos = search('query', query)
                final_video_list += videos
                query_search(query)

                # itera por cada resultado e faz uma busca de relacionados para cada
                for video in videos:
                    # Level 2
                    videos2 = search('related', video[0])
                    final_video_list += videos2
                    level_2 += videos2

                    # itera por cada resultado e faz uma busca de relacionados para
                    # cada um mais uma vez
                    for vd in level_2:
                        # level 3
                        videos3 = search('related', vd[0])
                        final_video_list += videos3


        else:
            # caso a profundidade nao seja informada
            return render_template("coletar.html", msg="verifique a profundidade")


        # renderiza a pagina
        return redirect("/resultados")
        #return render_template("results.html", videos=final_video_list)


@app.route("/analisar")
def analisar():
    """
    Cria uma visualização usando os dados coletados
    """

    # render the page
    return render_template("analisar.html")

@app.route("/resultados")
def resultados():
    """
    Cria uma pagina mostrando os videos coletados
    """

    # cria uma lista para armazenar dados
    videos = []
    contador = Counter()

    # abre o arquivo e le os dados
    with open('static/nodes.csv', 'r') as csvfile2:
        reader2 = csv.reader(csvfile2, delimiter=',')

        for row2 in reader2:
            if row2[0] != 'video_id':
                if row2[0] != 'query result':
                    line2 = [row2[0], row2[1], row2[2], row2[4], row2[5], row2[6]]
                    videos.append(line2)

    for entrada in videos:
        contador[entrada[0]] += 1

    lista_unica = []
    lista_final = []

    for video in videos:
        if video[0] not in lista_unica:
            n_video = video
            n_video.append(contador[video[0]])
            lista_final.append(n_video)
            lista_unica.append(video[0])


    # render the page
    return render_template("resultados.html", videos=lista_final)

@app.route("/config", methods=["GET", "POST"])
def config():
    """
    Renderiza uma página de configurações
    Post: permite alterar a chave da API e o maxresults
    """

    # mostra a pagina
    if request.method == "GET":
        return render_template("config.html")

    # se forem feitas alteracoes nas configuracoes
    else:
        radio = request.form.get("radio")
        api_field = request.form.get("newapi")
        mr_field = request.form.get("maxresults")

        # para mudancas no max results
        if radio == "mr":
            if mr_field != None and mr_field != '':
                global MAX_RESULTS
                MAX_RESULTS = mr_field

                return render_template("config.html", msg="Numero de resultados alterado")

            else:
                return render_template("config.html", msg="Forneça um valor para a configuração")

        # mudancas na chave da API
        elif radio == "api":
            if api_field != None and api_field !='':
                global DEVELOPER_KEY
                DEVELOPER_KEY = api_field

                return render_template("config.html", msg="Chave da API alterada")
            else:
                return render_template("config.html", msg="Forneça um valor para a configuração")

        # Ao apagar os dados da tabela
        elif radio == "delete":

            # Apaga os dados das tabelas e dicionario
            from api import dict
            dict.clear()

            # cria um novo arquivo de nodes
            with open('static/nodes.csv', 'w', newline = '', encoding = 'utf8') as csvfile1:
                writer1 = csv.writer(csvfile1, lineterminator = '\n')
                writer1.writerow(['video_id',
                                  'video_name',
                                  'channel_title',
                                  'channel_id',
                                  'published_at',
                                  'thumbnail_url',
                                  'type'
                                  ])

            # cria um novo arquivo de edges
            with open('static/edges.csv', 'w', newline = '', encoding = 'utf8') as csvfile2:
                writer2 = csv.writer(csvfile2, lineterminator = '\n')
                writer2.writerow(['source',
                                  'source_name',
                                  'target',
                                  'target_name'
                                  ])

            return render_template("config.html", msg="Dados da tabela apagados")

        # Caso encontre um submit sem nenhum campo selecionado
        elif radio == None:
            return render_template("config.html", msg="Selecione um campo para alterar")


@app.route("/results/<id>", methods=["GET", "POST"])
def results(id):
    """
    Recebe o id de um video do youtube e pega os seus relacionados
    os resultados sao exibidos para o usuario

    """

    videos = search('related', id)

    return render_template("results.html", videos=videos)

@socketio.on('get_nodes')
def get_nodes():
    '''
    Manda os dados dos nodes para o usuario via socket-io
    Faz a leitura a partir do arquivo csv
    '''

    # cria uma lista para armazenar dados
    nodes = []

    # cria uma lista para checagem de nodes duplicados
    node_check = []

    # abre o arquivo e le os dados
    with open('static/nodes.csv', 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            if row[0] != 'video_id':
                if row[0] not in node_check:
                    line = [row[0], row[1]]
                    nodes.append(line)
                    node_check.append(row[0])

    # emite os dados para o socket-io
    emit('get_nodes', nodes)


@socketio.on('get_edges')
def get_edges():
    '''
    Manda os dados dos edges para o usuario via socket-io
    Faz a leitura a partir do arquivo csv
    '''

    # cria uma lista para armazenar dados
    edges = []

    # abre o arquivo e le os dados
    with open('static/edges.csv', 'r') as csvfile2:
        reader2 = csv.reader(csvfile2, delimiter=',') # quotechar='|'
        for row2 in reader2:
            if row2[0] != 'source':
                line2 = [row2[0], row2[2]]
                edges.append(line2)

    # emite os dados para o socket-io
    emit('get_edges', edges)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)

# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
