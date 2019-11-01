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
from helpers import apology, apology_two, apology_three, login_required

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
#@app.after_request
#def after_request(response):
#    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
#    response.headers["Expires"] = 0
#    response.headers["Pragma"] = "no-cache"
#    return response

# Configura o database SQL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
db = SQLAlchemy(app)

# secret key
app.config["SECRET_KEY"] = os.getenv("KEY")

# teste da session
app.config["SESSION_PERMANENT"] = False


# Cria uma class para os usuarios
'''
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    hash = db.Column(db.String(80), unique=True, nullable=False)


    def __init__(self, username, hash):
        self.username = username
        self.hash = hash

    def check_password(self, password):
        return check_password_hash(self.hash, password)
'''


@app.route("/", methods=["GET", "POST"])
def index():
    """
    GET: Mostra a pagina inicial
    POST: Configura a API e manda para a página de busca
    """

    if request.method == "GET":

        # mostra a pagina inicial
        return render_template("index.html",
                                page='index'
                                )

    elif request.method == "POST":

        #configura a api
        api_field = request.form.get("newapi")
        rdio = request.form.get("mode")

        # guarda a API ou gera um erro se não houver API
        if api_field != None and api_field !='':
            session['developer_key'] = api_field
        else:
            return render_template("index.html",
                                    msg="Forneça chave da API",
                                    page='index'
                                    )
        # apaga a tabela - ou cria uma se não existir
        apagar()

        # passa para a proxima fase
        return redirect("/coletar")

'''
@app.route("/login", methods=["GET", "POST"])
def login():
    """Faz o log in"""

    # apaga dados da sessão
    session.clear()

    # Qaundo receber os dados (via POST)
    if request.method == "POST":

        #pega os dados
        username = request.form.get("username")
        password = request.form.get("password")

        # Verifica se há um nome de usuário
        if not username:
            return apology("usuário vazio", 403)

        # Verifica se realmente há uma senha
        elif not password:
            return apology("senha vazia", 403)

        # Busca o usuario no banco de dados e verifica a senha
        user = User.query.filter_by(username=username).first()
        password_check = user.check_password(password)

        # Verifica se as senhas conferem
        if password_check == True:
            session["user_id"] = user.id
            session["username"] = user.username
        else:
            return apology("usuário ou senha inválida", 403)

        # Roda a função apagar para criar tabelas
        apagar()

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

    # apaga os Dados
    apagar()

    # Redireciona para a pagina inicial
    return redirect("/")

@app.route("/registrar", methods=["GET", "POST"])
def registrar():
    """Register user"""

     # limpa os dados da sessão
    session.clear()

    # Ao enviar dados via POST
    if request.method == "POST":

        # pega os dados da pagina
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Verifica se ha um nome de usuario
        if not request.form.get("username"):
            return apology("crie um nome de usuário", 403)

        # Verifica se ha uma senha
        elif not request.form.get("password"):
            return apology("crie uma senha", 403)

         # Verifica se as senhas conferem
        if password != confirmation:
            return apology("Senhas diferentes", 403)

        # criptografia da senha
        hash_password = generate_password_hash(password)

        # verifica se já existe um usuário com esse username no banco de dados
        username_query = User.query.filter_by(username=username).first()

        # Se for um nome unico adiciona ao banco, senao mostra o erro
        if not username_query:
            new_user = User(username, hash_password)
            db.session.add(new_user)
            db.session.commit()
        else:
            return apology("usuario ja existe", 403)

        # Busca o usuario no banco de dados
        user = User.query.filter_by(username=username).first()

        # faz o login
        session["user_id"] = user.id
        session["username"] = user.username

        # roda a funcao apagar para criar tabelas
        apagar()

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
        if not new_password:
            return apology("Coloque uma senha nova", 403)

        # verifica se as novas senhas sao iguais
        if new_password != new_password_check:
            return apology("Senhas diferentes", 403)

        # encontra o usuario no banco de dados
        user = User.query.filter_by(id=session["user_id"]).first()
        check_pw = user.check_password(current_password)

        # se a sena atual for correta:
        if check_pw == True:

            # criptografa a senha
            user.hashp = generate_password_hash(new_password)

            # adiciona ao banco
            db.session.add(user)
            db.session.commit()

        # redireciona para a home
        return redirect("/")

    # carrega a pagina (get)
    else:
        return render_template("senha.html")
'''

@app.route("/coletar", methods=["GET", "POST"])
#@login_required
def coletar():
    """
    GET: Mostra a pagina com formulario para a coleta
    POST: preforma a busca na API e mostra os resultados

    O prceso é o mesmo da navegacao, mas e possivel fazer em diferentes
    niveis de profundidade:
    nivel 1: apenas resultados de uma busca.
    nivel 2: resultados de busca e suas recomendacoes
    nivel 3: resultados de busca, recomendacoes e recomendacoes subsequentes

    o modo de ampliação da busca funciona pegando ids de uma busca ja realizada
    e bucando os relacionados deles
    """
    page = 'coletar'

    # GET request
    if request.method == "GET":

        # pega nos e ids - verifica a possibilidade de ampliacao da busca
        numeros = []
        ids = []

        # nome do arquivo de nos
        nome_nodes = 'static/' + session['developer_key'] + '-nodes.csv'

        # abre o arquivo e le os dados
        with open(nome_nodes, 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')

            for row in reader:
                # ignora o cabecalho
                if row[0] != 'video_id':
                    # adiciona os videos a lista
                    numeros.append(row[7])
                    ids.append(row[0])


        if '1' in numeros:
            if '2' not in numeros:
                return render_template("coletar2.html", page=page)
            if '3' not in numeros:
                return render_template("coletar2.html", page=page)
            else:
                return apology_three("Não é possível coletar mais dados", page=page)


        return render_template("coletar.html", page=page)

    # POST request
    elif request.method == "POST":

        # pega ids - necessarios caso seja uma ampliação
        numeros = []
        ids = []
        prof_amp = 0

        # nome do arquivo de nos
        nome_nodes = 'static/' + session['developer_key'] + '-nodes.csv'

        # abre o arquivo e le os dados
        with open(nome_nodes, 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')

            for row in reader:
                # ignora o cabecalho
                if row[0] != 'video_id':
                    # adiciona os videos a lista
                    numeros.append(row[7])


        if '2' in numeros:
            with open(nome_nodes, 'r') as csvfile2:
                reader2 = csv.reader(csvfile2, delimiter=',')

                for row2 in reader2:
                    if row2[7] == '2':
                        ids.append(row2[0])
                        prof_amp = 3
        else:
            with open(nome_nodes, 'r') as csvfile2:
                reader2 = csv.reader(csvfile2, delimiter=',')

                for row2 in reader2:
                    if row2[7] == '1':
                        ids.append(row2[0])
                        prof_amp = 2

        # lista final a ser retornada
        final_video_list = []

        # o selector pode ter valores de 'query' ou 'seed'
        selector = request.form.get("radio")

        # pega os dados de profundidade e resultados por busca
        profundidade = request.form.get("profundidade")
        mr_field = request.form.get("maxresults")

        # para mudancas no max results
        if mr_field != None and mr_field != '':
            session['max_results'] = mr_field

        # verificacoes de seguranca

        # caso nenhum modo de busca seja selecionado
        if selector == None:
            msg = "selecione um modo de busca"
            return render_template("coletar.html", msg=msg, page=page)

        # caso a profundidade nao seja informada
        if profundidade == '':
            msg = "verifique a profundidade"
            return render_template("coletar.html", msg = msg, page=page)

        # pega os dados da pagina
        if selector == 'seed':
            query = request.form.get("videoid")
        elif selector == 'query':
            query = request.form.get("query")
################################################################################
        # caso seja uma amplicacao da busca ja existente!
        elif selector == 'ampliar':

            #if profundidade == '2':
                #if selector == 'seed':
            for id in ids:
                videos = search('related', id, prof_amp)

            return redirect("/resultados")

################################################################################

        if query == '':
            # caso não haja um termo de busca
            msg = "verifique o termo buscado"
            return render_template("coletar.html", msg=msg, page=page)



        # varia de acordo com a profundidade
        if profundidade == '1':
            if selector == 'seed':

                videos = search('related', query, 1)

            elif selector == 'query':
                print(session['developer_key'])
                videos = search('query', query, 1)

        elif profundidade == '2':

            # Faz a busca e coloca os resultados na lista
            if selector == 'seed': # level 1
                videos = search('related', query, 1)

                # itera por cada resultado e faz uma busca de relacionados
                for video in videos: # level 2
                    videos2 = search('related', video[0], 2)

            elif selector == 'query': # level 1
                videos = search('query', query, 1)

                # itera por cada resultado e faz uma busca de relacionados
                for video in videos: # level 2
                    videos2 = search('related', video[0], 2)


        elif profundidade == '3':

            level_2 = []

            # Faz a busca e coloca os resultados na lista
            if selector == 'seed': # level 1
                videos = search('related', query, 1)

                # itera por cada resultado e faz uma busca de relacionados
                for video in videos: # level 2
                    videos2 = search('related', video[0], 2)
                    level_2 += videos2

                    # itera por cada resultado e faz uma busca de relacionados
                    # para cada um mais uma vez
                    for vd in level_2: # level 3
                        videos3 = search('related', vd[0], 3)

            elif selector == 'query': # level 1
                videos = search('query', query, 1)

                # itera por cada resultado e faz uma busca de relacionados
                for video in videos: # Level 2
                    videos2 = search('related', video[0], 2)
                    level_2 += videos2

                    # itera por cada resultado e faz uma busca de relacionados
                    # para cada um mais uma vez
                    for vd in level_2: # level 3
                        videos3 = search('related', vd[0], 3)


        # renderiza a pagina
        return redirect("/resultados")


@app.route("/analisar")
#@login_required
def analisar():
    """
    Cria uma visualização usando os dados coletados
    a parte que controla os dados está em get_nodes e get_edges
    os dados são passados para a pagina via SocketIO
    """

    videos = []

    # nome do arquivo de nos
    nome_nodes = 'static/' + session['developer_key'] + '-nodes.csv'

    # abre o arquivo e le os dados
    with open(nome_nodes, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')

        for row in reader:
            # ignora o cabecalho
            if row[0] != 'video_id':
                # adiciona os videos a lista
                line = [row[0],
                        row[1],
                        row[2],
                        row[4],
                        row[5],
                        row[6]
                        ]
                videos.append(line)

    if len(videos) == 0:
        return apology_two("Não há dados para mostrar", page='analisar')

    # Renderiza a página
    return render_template("analisar.html", page='analisar')



@app.route("/resultados")

#@login_required
def resultados():
    """
    Cria uma pagina mostrando os videos coletados
    A funcao pode ou nao receber um video_id
    caso nao receba, ela carrega os resultados gerais
    caso ela receba, ela mostra os relacionados daquele video específico

    O modo POST mostra apenas os videos seeds
    """



    # le todos os dados da tabela de nos
    # conta quantas vezes cada vídeo aparece
    # cria uma lista sem elementos repetidos

    # cria uma lista para armazenar dados
    videos = []
    edges = set()
    recomendados = []
    contador = Counter()

    # nome do arquivo de nos
    nome_nodes = 'static/' + session['developer_key'] + '-nodes.csv'

    # abre o arquivo e le os dados
    with open(nome_nodes, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')

        for row in reader:
            # ignora o cabecalho
            if row[0] != 'video_id':
                # adiciona os videos a lista
                line = [row[0],
                        row[1],
                        row[2],
                        row[4],
                        row[5],
                        row[6]
                        ]
                videos.append(line)

    # Agora com os edges
    nome_edges = 'static/' + session['developer_key'] + '-edges.csv'

    # abre o arquivo e le os dados
    with open(nome_edges, 'r') as csvfile2:
        reader2 = csv.reader(csvfile2, delimiter=',')

        # remove o cabecalho pega os recomendados
        for row in reader2:
            if row[0] != 'source':
                #if row[0] == id:
                    # caso seja o id do video, pega os relacionados
                edges.add((row[0], row[2]))

    # faz a contagem
    for entrada in edges:
        contador[entrada[1]] += 1

    lista_unica = []
    lista_final = []

    # retira videos repetidos
    for video in videos:
        if video[0] not in lista_unica:
            # o n_video conta o numero de vezes que cada
            # video aparece no dataset
            n_video = video

            n_video.append(contador[video[0]])
            #n_video.append(contador[video])

            lista_final.append(n_video)
            lista_unica.append(video[0])

    # verifica se há dados
    if len(lista_final) == 0:
        return apology_two("Não há dados para mostrar",
                            page='resultados'
                            )

    # render the page
    return render_template("resultados.html",
                            videos=lista_final,
                            page='resultados'
                            )


@app.route("/navegar")
@app.route("/navegar/<id>")
@app.route("/navegar/<id>/<id2>")
def navegar(id = None, id2 = None):

    # ESSA FUNÇÃO VAI PASSAR A PROCURAR APENAS NO NIVEL 2! if row[7] == '1':
    if id != None:

        if id2 != None:
            #pass

            videos = [] # seeds
            videos2 = [] # relacionados
            videos3= [] # agora essa é a lista com os dados dos videos
            # usada para remover itens duplicados
            checklist = []
            checklist2 = []
            # lista retornada no final da função
            lista_final = []

            #nome dos arquivos
            nome_edges = 'static/' + session['developer_key'] + '-edges.csv'
            nome_nodes = 'static/' + session['developer_key'] + '-nodes.csv'

            # 1 - PEGA OS ID's DOS RELACIONADOS AO ID NA LISTA DE EDGES
            # abre o arquivo e le os dados
            with open(nome_edges, 'r') as csvfile:
                reader = csv.reader(csvfile, delimiter=',')

                # remove o cabecalho e procura o id correto
                for row in reader:
                    if row[0] != 'source':
                        if row[0] == id:
                            video_name1=row[1]
                            # caso seja o id do video, pega os relacionados
                            videos.append(row[2])


            with open(nome_edges, 'r') as csvfile:
                reader2 = csv.reader(csvfile, delimiter=',')

                # Procurar o ID 2 na lista de relacionados do ID 1
                # REPETIR esse procedimento para pegar os relacionados ao ID 2
                for row2 in reader2:

                    # remove o cabecalho e procura o id correto
                    if row2[0] in videos:
                        if row2[0] == id2:
                            video_name2=row2[1]
                            if row2[2] not in checklist2:
                                # caso seja o id do video, pega relacionados
                                videos2.append(row2[2])
                                checklist2.append(row2[2])


            # 2 - E AGORA OS DADOS DESSES RELACIONADOS DE RELACIONADOS
            # abre o arquivo e le os dados
            with open(nome_nodes, 'r') as csvfile2:
                reader3 = csv.reader(csvfile2, delimiter=',')

                # pega os dados dos videos relacionados
                for row3 in reader3:
                    if row3[0] != 'video_id':
                        if row3[0] in videos2:
                            if row3[0] not in checklist:
                                line = [row3[0],
                                        row3[1],
                                        row3[2],
                                        row3[4],
                                        row3[5],
                                        row3[6],
                                        row3[7]
                                        ]
                                videos3.append(line)
                                checklist.append(row3[0])


            if len(videos3) == 0:
                msg = "não há dados de relacionados para este video"
                return render_template("navegar-sem-dados.html", msg=msg, page='navegar')

            return render_template("navegar2.html",
                                    profundidade = '3',
                                    videos=videos3,
                                    id1=id,
                                    id2=id2,
                                    video_name1=video_name1,
                                    video_name2=video_name2,
                                    page='navegar'
                                    )



        # PARA A BUSCA COM APENAS 1 ID
        else:
            videos = []
            videos2 = []
            checklist = []
            lista_final = []
            video_name = ''

            #nome do arquivo
            nome_edges = 'static/' + session['developer_key'] + '-edges.csv'

            # abre o arquivo e le os dados
            with open(nome_edges, 'r') as csvfile:
                reader = csv.reader(csvfile, delimiter=',')

                # remove o cabecalho e procura o id correto
                for row in reader:
                    if row[0] != 'source':
                        if row[0] == id:
                            # caso seja o id do video, pega os relacionados
                            videos.append(row[2])
                            video_name = row[1]

            # variavel com o nome do arquivo
            nome_nodes = 'static/' + session['developer_key'] + '-nodes.csv'

            # abre o arquivo e le os dados
            with open(nome_nodes, 'r') as csvfile2:
                reader2 = csv.reader(csvfile2, delimiter=',')

                # pega os dados dos videos relacionados
                for row in reader2:
                    if row[0] != 'video_id':
                        if row[0] in videos:
                            if row[0] not in checklist:
                                line = [row[0],
                                        row[1],
                                        row[2],
                                        row[4],
                                        row[5],
                                        row[6],
                                        row[7]
                                        ]
                                videos2.append(line)
                                checklist.append(row[0])

            #print(videos2)
            for video in videos:
                for v2 in videos2:
                    if video == v2[0]:
                        linha = v2
                        lista_final.append(linha)

            if len(lista_final) == 0:
                msg = "não há dados de relacionados para este video"
                return render_template("navegar-sem-dados.html",
                                        msg=msg,
                                        page='navegar'
                                        )

            return render_template("navegar1.html",
                                    profundidade = '2',
                                    videos=lista_final,
                                    id1=id,
                                    video_name=video_name,
                                    page='navegar'
                                    )

    # quando o usuario clica no botão de seeds (POST)
    else:

        # lista de videos seed - serao mostrados na pagina
        videos = []

        # variavel com o nome do arquivo
        nome_nodes = 'static/' + session['developer_key'] + '-nodes.csv'

        # abre o arquivo e le os dados
        with open(nome_nodes, 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')

            # remove o cabecalho e procura videos no nivel 1
            for row in reader:
                if row[7] != 'depht':
                    if row[7] == '1':

                        # adiciona os dados a lista que ira para a pagina
                        line = [row[0],
                                row[1],
                                row[2],
                                row[4],
                                row[5],
                                row[6],
                                row[7]
                                ]
                        videos.append(line)

        # verifica se há dados
        if len(videos) == 0:
            return apology_two("Não há dados para mostrar",
                                page='navegar'
                                )

        # renderiza a pagina
        return render_template("navegar.html",
                                videos = videos,
                                profundidade = '1 (seeds)',
                                page='navegar'
                                )


@app.route("/tabelas")
#@login_required
def tabelas():
    """
    Renderiza uma página para baixar as tabelas
    """

    # mostra a pagina
    #if request.method == "GET":
    nodes = 'static/' + session['developer_key'] + '-nodes.csv'
    edges = 'static/' + session['developer_key'] + '-edges.csv'
    return render_template("tabelas.html",
                            nodes=nodes,
                            edges=edges,
                            page='tabelas'
                            )


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
#@login_required
def apagar():
    """
    Apaga os dados salvos na tabela
    """

    # Limpa o DICT com dados temporarios
    DICT.clear()

    # configura os nomes dos arquivos
    nome_nodes = 'static/' + session['developer_key'] + '-nodes.csv'
    nome_edges = 'static/' + session['developer_key'] + '-edges.csv'

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
    #return render_template("tabelas.html", msg="Dados das tabelas apagados")
    return redirect("/coletar")


@socketio.on('get_nodes')
def get_nodes():
    '''
    Manda os dados dos nodes para o usuario via socket-io
    Faz a leitura a partir do arquivo csv
    '''

    # cria o set
    edges = set()

    # cria um contador
    contador = Counter()

    # cria uma lista para armazenar dados
    nodes = []

    # cria uma lista para checagem de nodes duplicados
    node_check = []

    # nome do arquivo
    nome_nodes = 'static/' + session['developer_key'] + '-nodes.csv'

    # abre o arquivo e le os dados
    with open(nome_nodes, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            if row[0] != 'video_id':
                #if row[0] not in node_check:
                if row[7] == '1':
                    line = [row[0], row[1], '#095F95']
                else:
                    line = [row[0], row[1], '#000000']
                nodes.append(line)
                #node_check.append(row[0])

    # Agora com os edges
    nome_edges = 'static/' + session['developer_key'] + '-edges.csv'

    # abre o arquivo e le os dados
    with open(nome_edges, 'r') as csvfile2:
        reader2 = csv.reader(csvfile2, delimiter=',')

        # remove o cabecalho pega os recomendados
        for row in reader2:
            if row[0] != 'source':
                #if row[0] == id:
                    # caso seja o id do video, pega os relacionados
                edges.add((row[0], row[2]))

    # faz a contagem
    for entrada in edges:
        contador[entrada[1]] += 1

    lista_unica = []
    lista_final = []


    # retira videos repetidos
    for video in nodes:
        if video[0] not in lista_unica:
            # o n_video conta o numero de vezes que cada
            # video aparece no dataset
            '''
            ao invés do append(contador[video]) criar condições para adicionar
            os valores do tamanho e cor a lista_final
            if contador[video] == 1:
                size = 1
                n_video.append(size)
            elif 1 < contador < 10:
                size = 2
                n_video.append(size)
            '''
            n_video = video


            if contador[video[0]] <= 1:
                size = 1
                if video[2] == '#000000':
                    n_video[2] = '#cc9900'
                    #print(n_video)

                n_video.append(size)
                #print(n_video)
            elif 2 <= contador[video[0]] < 4:
                size = 2
                if video[2] == '#000000':
                    n_video[2] = '#ff9933'

                n_video.append(size)
            elif 4 <= contador[video[0]] < 6:
                size = 3

                if video[2] == '#000000':
                    n_video[2] = '#ff6600'

                n_video.append(size)
            elif 6 <= contador[video[0]] < 8:
                size = 4

                if video[2] == '#000000':
                    n_video[2] = '#cc0000'

                n_video.append(size)
            elif contador[video[0]] >= 8:
                size = 5

                if video[2] == '#000000':
                    n_video[2] = '#660033'


                n_video.append(size)

            #n_video.append(contador[video[0]])
            lista_final.append(n_video)
            lista_unica.append(video[0])



    # emite os dados para o socket-io
    emit('get_nodes', lista_final)


@socketio.on('get_edges')
def get_edges():
    '''
    Manda os dados dos edges para o usuario via socket-io
    Faz a leitura a partir do arquivo csv
    '''

    # cria uma lista para armazenar dados
    edges = []

    # nome do arquivo de edges
    nome_edges = 'static/' + session['developer_key'] + '-edges.csv'

    # abre o arquivo e le os dados
    with open(nome_edges, 'r') as csvfile2:
        reader2 = csv.reader(csvfile2, delimiter=',') # quotechar='|'
        for row2 in reader2:
            if row2[0] != 'source':
                if row2[0] != 'query result':
                    line2 = [row2[0], row2[2]]
                    edges.append(line2)

    # emite os dados para o socket-io
    emit('get_edges', edges)



################################################################################
# FUNCAO DE BUSCA DO YOUTUBE
################################################################################
def search(mode, query, profundidade):
    """
    Funcao que faz a busca na api do YOUTUBE
    Recebe 4 valores:

    primeiro:
    "query" faz uma pesquisa por um termo ou "related" para videos relacionados

    segundo:
    termo a ser buscado ou id do vídeo a ser enviado para a api_field

    terceiro:
    se o savemode for False os dados não serão registrados nas tabelas

    quarto:
    profundidade da busca. 1 pega apenas resultados da busca enquanto 3
    pega resultados da busca, seus relacionados e relacionados dos relacionados

    Retorna:
    uma lista com os vídeos recebidos da API
    Também sao criadas duas tabelas csv que serão usadas em outras partes do app

    os dados podem ser mantidos no DICT para evitar que uma consulta ao mesmo
    video seja feita duas vezes, evitando o gasto da cota da API

    """

    # aviavel usada para contar a quantidade de
    # respostas em cada chamada da api
    contador_loop = 0

    #test
    session['developer_key']

    # configuracao da API
    youtube = build(YOUTUBE_API_SERVICE_NAME,
                    YOUTUBE_API_VERSION,
                    developerKey=session['developer_key']
                    )

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

        # usa apenas os vídeos recomendados, ignora canais e playlists
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
                        search_result["snippet"]["title"]
                        ]
            # se for uma busca por termo, coloca o termo na tabela para referencia
            '''
            elif mode == 'query':
                # cria um edge
                edge = ['query result',
                        'query: ' + query,
                        search_result["id"]["videoId"],
                        search_result["snippet"]["title"],
                        profundidade,
                        contador_loop
                        ]
            '''
            # verifica se o usuário prefere se os dados sejam salvos
            #if savemode == True:

            nome_nodes = 'static/' + session['developer_key'] + '-nodes.csv'
            nome_edges = 'static/' + session['developer_key'] + '-edges.csv'

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

            contador_loop += 1

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

if __name__ == '__main__':
    socketio.run(app)
