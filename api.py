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


# creates a dict for storage
dict = {}


'''
# funcao para a aba de navegacao
def ytnav(query, seed):


        # caso seja uma busca de um seed, faz uma busca passando o related video id
        if seed == True:
            videos = related_search(query)
            return videos
        else:
            videos = query_search(query)
            return videos

# funcao para a aba de coleta de videos
def ytcollect(query, seed): #, profundidade

    final_video_list = []

    videos = query_search(query)
    final_video_list += videos

    for video in videos:
        videos2 = related_search(video[2])
        final_video_list += videos2

    return final_video_list


'''

def related_search(video_id):

        videos = []

        # O MAX RESULTS PRECISA SER ADICIONADO NA PAGINA HTML
        search_response = youtube.search().list(relatedToVideoId=video_id,
                                    part="id,snippet",
                                    maxResults=5,
                                    type='video').execute()

        # ITERA PELOS RESUTADOS DA BUSCA E ADICIONA A LISTA
        for search_result in search_response.get("items", []):

            # usa apenas os vídeos recomendados, ignora canais e playlists (por enquanto)
            if search_result["id"]["kind"] == "youtube#video":
                list = [video_id, # 'query result', #video_id,
                        search_result["snippet"]["title"],
                        search_result["id"]["videoId"],
                        search_result["snippet"]["channelTitle"],
                        search_result["snippet"]["channelId"],
                        search_result["snippet"]["publishedAt"],
                        search_result["snippet"]["thumbnails"]["default"]["url"],
                        "video"
                        ]
                videos.append(list)
                #print(list)

                # add data to CSV file
                with open('static/output.csv', 'a', newline = '', encoding = 'utf8') as csvfile:
                    writer = csv.writer(csvfile, lineterminator = '\n')
                    writer.writerow(list)


        # render the page
        #return render_template("results.html", videos=videos)
        return videos


def query_search(query):

        videos = []

        search_response = youtube.search().list(q=query, part="id,snippet").execute()

        # ITERA PELOS RESUTADOS DA BUSCA E ADICIONA A LISTA
        for search_result in search_response.get("items", []):

            # usa apenas os vídeos recomendados, ignora canais e playlists (por enquanto)
            if search_result["id"]["kind"] == "youtube#video":
                list = ['query result',
                        search_result["snippet"]["title"],
                        search_result["id"]["videoId"],
                        search_result["snippet"]["channelTitle"],
                        search_result["snippet"]["channelId"],
                        search_result["snippet"]["publishedAt"],
                        search_result["snippet"]["thumbnails"]["default"]["url"],
                        "video"
                        ]
                videos.append(list)
                #print(list)

                # add data to CSV file
                with open('static/output.csv', 'a', newline = '', encoding = 'utf8') as csvfile:
                    writer = csv.writer(csvfile, lineterminator = '\n')
                    writer.writerow(list)


        # render the page
        #return render_template("results.html", videos=videos)
        return videos
