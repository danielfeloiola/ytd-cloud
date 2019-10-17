# IMPORT STATEMENTS (DUH!)
import csv
import os
from collections import Counter
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session, send_file
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from flask_socketio import SocketIO, emit
from helpers import apology, login_required

# API do Google
from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser

# VARIAVEIS GLOBAIS

# cria um dict para armazenamento
# se um video já foi pedido para a api, ele verifica antes o dict para evitar
# um request do mesmo vídeo
DICT = {}

# armazena video ids e os nomes
VIDEO_NAMES = {}

# Para a configuração da API
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# Configura a aplicacao
app = Flask(__name__)

# socketio
socketio = SocketIO(app)

# auto-reload
app.config["TEMPLATES_AUTO_RELOAD"] = True

# response cache
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configura o database SQL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
db = SQLAlchemy(app)

# secret key
app.config['SECRET_KEY'] = os.environ['KEY']


# Cria uma class para os usuarios
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    hash = db.Column(db.String(80), unique=True, nullable=False)


    def __init__(self, username, hash):
        self.username = username
        self.hash = hash

    def check_password(self, password):
        return check_password_hash(self.hash, password)



@app.route("/", methods=["GET", "POST"])
def index():
    """
    GET: Mostra a pagina inicial
    POST: Configura a API e manda para a página de busca
    """

    if request.method == "GET":

        # mostra a pagina inicial
        return render_template("index.html")

    elif request.method == "POST":

        #configura a api
        api_field = request.form.get("newapi")
        rdio = request.form.get("mode")

        # guarda a API ou gera um erro se não houver API
        if api_field != None and api_field !='':
            session['developer_key'] = api_field
        else:
            return render_template("index.html", msg="Forneça chave da API")

        # passa para a proxima fase
        return redirect("/coletar")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Faz o log in"""

    # apaga dados da sessão
    session.clear()

    # Qaundo receber os dados (via POST)
    if request.method == "POST":

        # Verifica se há um nome de usuário
        if not request.form.get("username"):
            return apology("usuário vazio", 403)

        # Verifica se realmente há uma senha
        elif not request.form.get("password"):
            return apology("senha vazia", 403)

        # Busca o usuario no banco de dados e verifica a senha
        user = User.query.filter_by(username=request.form.get("username")).first()
        password_check = user.check_password(request.form.get("password"))

        # Verifica se as senhas conferem
        if password_check == True:
            session["user_id"] = user.id
            session["username"] = user.username
        else:
            return apology("usuário ou senha inválida", 403)

        # Redireciona para a homepage
        return redirect("/")

    # Se o usuário está procurando o formulario - GET
    else:
        return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    """Faz o logout"""

    # Apaga a sessao
    session.clear()

    # Redireciona para a pagina inicial
    return redirect("/")

@app.route("/registrar", methods=["GET", "POST"])
def registrar():
    """Register user"""

     # limpa os dados da sessão
    session.clear()

    # Ao enviar dados via POST
    if request.method == "POST":

        # Verifica se ha um nome de usuario
        if not request.form.get("username"):
            return apology("crie um nome de usuário", 403)

        # Verifica se ha uma senha
        elif not request.form.get("password"):
            return apology("crie uma senha", 403)

         # Verifica se as senhas conferem
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("Senhas diferentes", 403)

        # criptografia da senha
        hash_password = generate_password_hash(request.form.get("password"))

        # configura o usrname
        username = request.form.get("username")

        # verifica se já existe um usuário com esse username no banco de dados
        username_query = User.query.filter_by(username=request.form.get("username")).first()

        # Se for um nome unico adiciona ao banco, senao mostra o erro
        if not username_query:
            new_user = User(username, hash_password)
            db.session.add(new_user)
            db.session.commit()
        else:
            return apology("usuario ja existe", 403)

        #  faz o login
        session["user_id"] = user.id
        session["username"] = user.username

        # redireciona para a home page
        return redirect("/")

    # Se o usuário esta porcurando a pagina (via GET)
    else:
        return render_template("registrar.html")


@app.route("/senha", methods=["GET", "POST"])
@login_required
def senha():
    """Muda a senha"""

    if request.method == "POST":

        # Pega as senhas
        current_password = request.form.get("current-password")
        new_password = request.form.get("new-password")
        new_password_check = request.form.get("new-password-check")

        # Verifica se a senha não está em branco
        if not request.form.get("new-password"):
            return apology("Coloque uma senha nova", 403)

        # verifica se as novas senhas sao iguais
        if new_password != new_password_check:
            return apology("Senhas diferentes", 403)

        # encontra o usuario no banco de dados
        user = User.query.filter_by(id=session["user_id"]).first()
        check_pw = user.check_password(request.form.get("current-password"))

        # se a sena atual for correta:
        if check_pw == True:

            # criptografa a senha
            user.hashp = generate_password_hash(request.form.get("new-password"))

            # adiciona ao banco
            db.session.add(user)
            db.session.commit()

        # redireciona para a home
        return redirect("/")

    # carrega a pagina (get)
    else:
        return render_template("senha.html")


@app.route("/coletar", methods=["GET", "POST"])
@login_required
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

        # o selector pode ter valores de 'query' ou 'seed'
        selector = request.form.get("radio")

        # pega os dados da pagina
        if selector == 'seed':
            query = request.form.get("videoid")
        elif selector == 'query':
            query = request.form.get("query")

        # pega os dados de profundidade e resultados por busca
        profundidade = request.form.get("profundidade")
        mr_field = request.form.get("maxresults")

        # mudancas no max results
        if mr_field != None and mr_field != '':
            session['max_results'] = mr_field
            #global MAX_RESULTS
            #MAX_RESULTS = mr_field

        # lista final a ser retornada
        final_video_list = []

        # PRECISA DE UMA PROTECAO PARA EVITAR QUE UMA BUSCA SEM O RADIO MARCADO
        # RETORNE UM ERRO 500
        '''
        ######################################################################################
        '''
        # se nao for introduzido um termo ou video_id - retorna um erro

        if query == '':
            # caso a profundidade nao seja informada
            return render_template("coletar.html", msg="verifique o termo buscado")

        # varia de acordo com a profundidade
        if profundidade == '1':
            #if radio == 'seed'
            if selector == 'seed':

                videos = search('related', query, True, 1)
                final_video_list += videos

            #elif radio == 'query'
            elif selector == 'query':

                videos = search('query', query, True, 1)
                final_video_list += videos

        elif profundidade == '2':

            # Faz a busca e coloca os resultados na lista
            if selector == 'seed': # level 1
                videos = search('related', query, True, 1)
                final_video_list += videos

                # itera por cada resultado e faz uma busca de relacionados para cada
                for video in videos: # level 2
                    videos2 = search('related', video[0], True, 2)
                    final_video_list += videos2

            elif selector == 'query': # level 1
                #print(session)
                videos = search('query', query, True, 1)
                final_video_list += videos

                # itera por cada resultado e faz uma busca de relacionados para cada
                for video in videos: # level 2
                    videos2 = search('related', video[0], True, 2)
                    final_video_list += videos2


        elif profundidade == '3':

            level_2 = []

            # Faz a busca e coloca os resultados na lista
            if selector == 'seed': # level 1
                videos = search('related', query, True, 1)
                final_video_list += videos

                # itera por cada resultado e faz uma busca de relacionados para cada
                for video in videos: # level 2
                    videos2 = search('related', video[0], True, 2)
                    final_video_list += videos2
                    level_2 += videos2

                    # itera por cada resultado e faz uma busca de relacionados para
                    # cada um mais uma vez
                    for vd in level_2: # level 3
                        videos3 = search('related', vd[0], True, 3)
                        final_video_list += videos3

            elif selector == 'query': # level 1
                videos = search('query', query, True, 1)
                final_video_list += videos

                # itera por cada resultado e faz uma busca de relacionados para cada
                for video in videos: # Level 2
                    videos2 = search('related', video[0], True, 2)
                    final_video_list += videos2
                    level_2 += videos2

                    # itera por cada resultado e faz uma busca de relacionados para
                    # cada um mais uma vez
                    for vd in level_2: # level 3
                        videos3 = search('related', vd[0], True, 3)
                        final_video_list += videos3


        else:
            # caso a profundidade nao seja informada
            return render_template("coletar.html", msg="verifique a profundidade")


        # renderiza a pagina
        return redirect("/resultados")


@app.route("/analisar")
@login_required
def analisar():
    """
    Cria uma visualização usando os dados coletados
    """

    # render the page
    return render_template("analisar.html")


@app.route("/resultados", methods=["GET", "POST"])
@app.route("/resultados/<id>")
def resultados(id = None):
    """
    Cria uma pagina mostrando os videos coletados
    Precida de mais comentários ##################################################################
    """

    if request.method =='GET':

        if id == None:
            # cria uma lista para armazenar dados
            videos = []
            contador = Counter()

            #nome do arquivo
            nome_nodes = 'static/' + session['username'] + '-nodes.csv'

            # abre o arquivo e le os dados
            with open(nome_nodes, 'r') as csvfile:
                reader = csv.reader(csvfile, delimiter=',')

                for row in reader:
                    if row[0] != 'video_id':

                        line = [row[0], row[1], row[2], row[4], row[5], row[6]]
                        videos.append(line)

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

            # verifica se há dados
            if len(lista_final) == 0:
                return apology("Não há dados")

            # render the page
            return render_template("resultados.html", videos=lista_final)

        elif id != None:
            # COMENTAR DIREITO ESSA PARTE DO CÓDIGO

            videos = []
            videos2 = []
            count = 1
            checklist = []
            lista_final = []

            #nome do arquivo
            nome_edges = 'static/' + session['username'] + '-edges.csv'

            # abre o arquivo e le os dados
            with open(nome_edges, 'r') as csvfile:
                reader = csv.reader(csvfile, delimiter=',')

                # remove o cabecalho e procura o id correto
                for row in reader:
                    if row[0] != 'source':
                        if row[0] == id:
                            videos.append(row[2])

            # variavel com o nome do arquivo
            nome_nodes = 'static/' + session['username'] + '-nodes.csv'

            # abre o arquivo e le os dados
            with open(nome_nodes, 'r') as csvfile2:
                reader2 = csv.reader(csvfile2, delimiter=',')

                for row in reader2:
                    if row[0] != 'video_id':
                        if row[0] in videos:
                            if row[0] not in checklist:
                                line = [row[0], row[1], row[2], row[4], row[5], row[6]]
                                videos2.append(line)
                                checklist.append(row[0])

            for video in videos:
                for v2 in videos2:
                    if video == v2[0]:
                        linha = v2
                        lista_final.append(linha)
                        count += 1


            if len(lista_final) == 0:
                msg = "não há dados de relacionados para este video"
                return render_template("resultados3.html", msg=msg)

            return render_template("resultados2.html", videos=lista_final)

    # quando o usuario clica no botão de seeds (POST)
    elif request.method =='POST':

        # lista de videos seed - serao mostrados na pagina
        videos = []

        # variavel com o nome do arquivo
        nome_nodes = 'static/' + session['username'] + '-nodes.csv'

        # abre o arquivo e le os dados
        with open(nome_nodes, 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')

            # remove o cabecalho e procura videos no nivel 1
            for row in reader:
                if row[7] != 'depht':
                    if row[7] == '1':

                        # adiciona os dados a lista que ira para a pagina
                        line = [row[0], row[1], row[2], row[4], row[5], row[6]]
                        videos.append(line)

        # verifica se há dados
        if len(videos) == 0:
            return apology("Não há dados")

        # renderiza a pagina
        return render_template("resultados2.html", videos = videos, profundidade = 'seeds')


@app.route("/tabelas")
@login_required
def tabelas():
    """
    Renderiza uma página para baixar as tabelas
    """

    # mostra a pagina
    #if request.method == "GET":
    return render_template("tabelas.html")


@app.route("/confirma")
@login_required
def confirma():
    """
    Confirma se o susario que apagar os dados
    """

    # mostra a pagina
    #if request.method == "GET":
    return render_template("confirma.html")



@app.route("/apagar")
@login_required
def apagar():
    """
    Apaga os dados salvos na tabela
    """

    # Limpa o DICT com dados temporarios
    DICT.clear()

    # configura os nomes dos arquivos
    nome_nodes = 'static/' + session['username'] + '-nodes.csv'
    nome_edges = 'static/' + session['username'] + '-edges.csv'

    # cria um novo arquivo de nodes
    with open(nome_nodes, 'w', newline = '', encoding = 'utf8') as csvfile1:
        writer1 = csv.writer(csvfile1, lineterminator = '\n')
        writer1.writerow(['video_id',
                          'video_name',
                          'channel_title',
                          'channel_id',
                          'published_at',
                          'thumbnail_url',
                          'type',
                          'depth'
                          ])

    # cria um novo arquivo de edges
    with open(nome_edges, 'w', newline = '', encoding = 'utf8') as csvfile2:
        writer2 = csv.writer(csvfile2, lineterminator = '\n')
        writer2.writerow(['source',
                          'source_name',
                          'target',
                          'target_name'
                          ])

    # mostra mensagem se sucesso
    return render_template("tabelas.html", msg="Dados das tabelas apagados")



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

    # nome do arquivo
    nome_nodes = 'static/' + session['username'] + '-nodes.csv'

    # abre o arquivo e le os dados
    with open(nome_nodes, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            if row[0] != 'video_id':
                if row[0] not in node_check:
                    if row[7] == '1':
                        line = [row[0], row[1], '#095F95']
                    else:
                        line = [row[0], row[1], '#000000']
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

    # nome do arquivo de edges
    nome_edges = 'static/' + session['username'] + '-edges.csv'

    # abre o arquivo e le os dados
    with open(nome_edges, 'r') as csvfile2:
        reader2 = csv.reader(csvfile2, delimiter=',') # quotechar='|'
        for row2 in reader2:
            if row2[0] != 'source':
                line2 = [row2[0], row2[2]]
                edges.append(line2)

    # emite os dados para o socket-io
    emit('get_edges', edges)

################################################################################
# FUNCAO DE BUSCA DO YOUTUBE
################################################################################

def search(mode, query, savemode, profundidade):
    """
    Colocar aqui uma docstring
    #############################################################################################
    """


    #youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=session['developer_key'])

    # lista com a resposta da api que será retornada
    videos = []

    # para busca de videos relacionados
    if mode == "related":

        # se o video ainda nao foi adicionado ao dicionario
        if query not in DICT:

            # faz a busca no youtube
            search_response = youtube.search().list(relatedToVideoId=query,
                                        part="id,snippet",
                                        maxResults=session['max_results'],
                                        type='video').execute()

        # se o vídeo já foi buscado na api usa os valores adicioandos ao DICT
        # para evitar gastos da cota da API
        else:

            # busca no dicionario
            search_response = DICT[query]

    # se for uma busca por um termo, faz a busca - nao passa pelo dicionario
    elif mode == "query":
        search_response = youtube.search().list(q=query,
                                                part="id,snippet",
                                                maxResults=session['max_results'],
                                                type='video').execute()


    # itera pelos resultados da busca e adiciona a lista
    for search_result in search_response.get("items", []):

        # usa apenas os vídeos recomendados, ignora canais e playlists (por enquanto)
        if search_result["id"]["kind"] == "youtube#video":

            if mode == 'related':
                #cria um node
                node = [search_result["id"]["videoId"],
                        search_result["snippet"]["title"],
                        search_result["snippet"]["channelTitle"],
                        search_result["snippet"]["channelId"],
                        search_result["snippet"]["publishedAt"],
                        search_result["snippet"]["thumbnails"]["default"]["url"],
                        "video relacionado",
                        profundidade
                        ]

            elif mode == 'query':
                #cria um node
                node = [search_result["id"]["videoId"],
                        search_result["snippet"]["title"],
                        search_result["snippet"]["channelTitle"],
                        search_result["snippet"]["channelId"],
                        search_result["snippet"]["publishedAt"],
                        search_result["snippet"]["thumbnails"]["default"]["url"],
                        "resultado de busca",
                        profundidade
                        ]

            # adiciona o node a lista de videos
            videos.append(node)

            # adiciona o video a lista com nomes de videos
            VIDEO_NAMES[search_result["id"]["videoId"]] = search_result["snippet"]["title"]

            # alterna entre query e related para a criacao de um edge
            # se for uma buca relacionada, coloca o video buscado
            if mode == 'related':
                # cria um edge
                edge = [query,
                        VIDEO_NAMES[query],
                        search_result["id"]["videoId"],
                        search_result["snippet"]["title"]]
            # se for uma busca por termo, coloca o termo na tabela para referencia
            '''
            elif mode == 'query':
                # cria um edge
                edge = ['query result',
                        'query: ' + query,
                        search_result["id"]["videoId"],
                        search_result["snippet"]["title"]]
            '''
            # verifica se o usuário prefere se os dados sejam salvos
            if savemode == True:

                nome_nodes = 'static/' + session['username'] + '-nodes.csv'
                nome_edges = 'static/' + session['username'] + '-edges.csv'

                if mode == 'related':
                    # adiciona o node a tabela de nodes
                    with open(nome_nodes, 'a', newline = '', encoding = 'utf8') as csvfile1:
                        writer1 = csv.writer(csvfile1, lineterminator = '\n')
                        writer1.writerow(node)

                    # adiciona o edge a tabela de edges
                    with open(nome_edges, 'a', newline = '', encoding = 'utf8') as csvfile2:
                        writer2 = csv.writer(csvfile2, lineterminator = '\n')
                        writer2.writerow(edge)

                if mode == 'query':
                    with open(nome_nodes, 'a', newline = '', encoding = 'utf8') as csvfile1:
                        writer1 = csv.writer(csvfile1, lineterminator = '\n')
                        writer1.writerow(node)

    # adiciona o video ao dict para evitar uma busca duplicada na API caso o videos
    # seja recomendado pela api mais uma vez
    if mode == 'related':
        # adiciona ao dicionario
        DICT[query] = search_response

    # retorna a lista de videos
    return videos


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)

# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
