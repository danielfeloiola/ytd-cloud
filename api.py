# API GOOGLE
from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser

# Bibliotecas
import os
import csv

# API
DEVELOPER_KEY = os.environ['API']
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)

# cria um dict para armazenamento
# se um video já foi pedido para a api, ele verifica antes o dict para evitar
# um request do mesmo vídeo
# precisa haver uma função para limpar o dicionario <<<
# ou colocar dentro da funcão de busca <<<
dict = {}

# armazena video ids e os nomes
video_names = {}

def related_search(video_id):

    # lista com a resposta da api que será retornada
    videos = []

    # IF IT IS THE FIRST TIME WE LOOK FOR THE VIDEO
    if video_id not in dict:

        # O MAX RESULTS PRECISA SER ADICIONADO NA PAGINA HTML
        search_response = youtube.search().list(relatedToVideoId=video_id,
                                    part="id,snippet",
                                    maxResults=5,
                                    type='video').execute()

    # Se o vídeo já foi buscado na api
    else:

        #busca no dicionario
        search_response = dict[video_id]

        # debug
        print("THIS WAS A DICT QUERY")
        print(search_response)

    # ITERA PELOS RESUTADOS DA BUSCA E ADICIONA A LISTA
    for search_result in search_response.get("items", []):

        # usa apenas os vídeos recomendados, ignora canais e playlists (por enquanto)
        if search_result["id"]["kind"] == "youtube#video":
            node = [#video_id, # 'query result', #video_id,
                    #video_names[video_id],
                    search_result["id"]["videoId"],
                    search_result["snippet"]["title"],
                    search_result["snippet"]["channelTitle"],
                    search_result["snippet"]["channelId"],
                    search_result["snippet"]["publishedAt"],
                    search_result["snippet"]["thumbnails"]["default"]["url"],
                    "video"
                    ]
            videos.append(node)

            video_names[search_result["id"]["videoId"]] = search_result["snippet"]["title"]

            edge = [video_id,
                    video_names[video_id],
                    search_result["id"]["videoId"],
                    search_result["snippet"]["title"]]
            #print(list)

            # adiciona os dados a tabela de nodes
            with open('static/nodes.csv', 'a', newline = '', encoding = 'utf8') as csvfile1:
                writer1 = csv.writer(csvfile1, lineterminator = '\n')
                writer1.writerow(node)

            # adiciona os dados a tabela de edges
            with open('static/edges.csv', 'a', newline = '', encoding = 'utf8') as csvfile2:
                writer2 = csv.writer(csvfile2, lineterminator = '\n')
                writer2.writerow(edge)


    # ADD TO DICT
    dict[video_id] = search_response

    #return render_template("results.html", videos=videos)
    return videos



def query_search(query):

    # lista com a resposta da api que será retornada
    videos = []

    search_response = youtube.search().list(q=query, part="id,snippet").execute()

    # ITERA PELOS RESUTADOS DA BUSCA E ADICIONA A LISTA
    for search_result in search_response.get("items", []):

        # usa apenas os vídeos recomendados, ignora canais e playlists (por enquanto)
        if search_result["id"]["kind"] == "youtube#video":
            node = [#'query result',
                    #'query: ' + query,
                    search_result["id"]["videoId"],
                    search_result["snippet"]["title"],
                    search_result["snippet"]["channelTitle"],
                    search_result["snippet"]["channelId"],
                    search_result["snippet"]["publishedAt"],
                    search_result["snippet"]["thumbnails"]["default"]["url"],
                    "video"
                    ]
            videos.append(node)

            video_names[search_result["id"]["videoId"]] = search_result["snippet"]["title"]

            edge = ['query result',
                    'query: ' + query,
                    search_result["id"]["videoId"],
                    search_result["snippet"]["title"]]
            #print(list)

            # adiciona os dados a tabela de nodes
            with open('static/nodes.csv', 'a', newline = '', encoding = 'utf8') as csvfile:
                writer = csv.writer(csvfile, lineterminator = '\n')
                writer.writerow(node)

            # adiciona os dados a tabela de edges
            with open('static/edges.csv', 'a', newline = '', encoding = 'utf8') as csvfile2:
                writer2 = csv.writer(csvfile2, lineterminator = '\n')
                writer2.writerow(edge)

    # render the page
    #return render_template("results.html", videos=videos)
    return videos
