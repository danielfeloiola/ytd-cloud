# API do Google
from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser


# Bibliotecas
import os
import csv

# cria um dict para armazenamento
# se um video já foi pedido para a api, ele verifica antes o dict para evitar
# um request do mesmo vídeo
# precisa haver uma função para limpar o dicionario <<< ######################################
dict = {}

# armazena video ids e os nomes
video_names = {}

def search(mode, query):

    # importa a chave da api
    from application import MAX_RESULTS, DEVELOPER_KEY

    # configura a API
    YOUTUBE_API_SERVICE_NAME = "youtube"
    YOUTUBE_API_VERSION = "v3"
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)

    # lista com a resposta da api que será retornada
    videos = []

    # para busca de videos relacionados
    if mode == "related":

        # se o video ainda nao foi adicionado ao dicionario
        if query not in dict:

            # faz a busca no youtube
            search_response = youtube.search().list(relatedToVideoId=query,
                                        part="id,snippet",
                                        maxResults=MAX_RESULTS,
                                        type='video').execute()

        # se o vídeo já foi buscado na api usa os valores adicioandos ao DICT
        # para evitar gastos da cota da API
        else:

            # busca no dicionario
            search_response = dict[query]

            # debug
            #print("THIS WAS A DICT QUERY")
            #print(search_response)

    # se for uma busca por um termo, faz a busca - nao passa pelo dicionario
    elif mode == "query":
        search_response = youtube.search().list(q=query, part="id,snippet").execute()


    # itera pelos resultados da busca e adiciona a lista
    for search_result in search_response.get("items", []):

        # usa apenas os vídeos recomendados, ignora canais e playlists (por enquanto)
        if search_result["id"]["kind"] == "youtube#video":

            #cria um node
            node = [search_result["id"]["videoId"],
                    search_result["snippet"]["title"],
                    search_result["snippet"]["channelTitle"],
                    search_result["snippet"]["channelId"],
                    search_result["snippet"]["publishedAt"],
                    search_result["snippet"]["thumbnails"]["default"]["url"],
                    "video"]

            # adiciona o node a lista de videos
            videos.append(node)

            # adiciona o video a lista com nomes de videos
            video_names[search_result["id"]["videoId"]] = search_result["snippet"]["title"]

            # alterna entre query e related para a criacao de um edge
            # se for uma buca relacionada, coloca o video buscado
            if mode == 'related':
                # cria um edge
                edge = [query,
                        video_names[query],
                        search_result["id"]["videoId"],
                        search_result["snippet"]["title"]]
            # se for uma busca por termo, coloca o termo na tabela para referencia
            elif mode == 'query':
                # cria um edge
                edge = ['query result',
                        'query: ' + query,
                        search_result["id"]["videoId"],
                        search_result["snippet"]["title"]]


            # adiciona o node a tabela de nodes
            with open('static/nodes.csv', 'a', newline = '', encoding = 'utf8') as csvfile1:
                writer1 = csv.writer(csvfile1, lineterminator = '\n')
                writer1.writerow(node)

            # adiciona o edge a tabela de edges
            with open('static/edges.csv', 'a', newline = '', encoding = 'utf8') as csvfile2:
                writer2 = csv.writer(csvfile2, lineterminator = '\n')
                writer2.writerow(edge)

    # adiciona o video ao dict para evitar uma busca duplicada na API caso o videos
    # seja recomendado pela api mais uma vez
    if mode == 'related':
        # adiciona ao dicionario
        dict[query] = search_response

    # retorna a lista de videos
    return videos
