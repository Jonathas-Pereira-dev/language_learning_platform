"""Consulta oficial de vídeos públicos; no inventa enlaces para países sin resultados."""
import json
import os
from urllib.request import Request,urlopen
from urllib.parse import urlencode
from podcasts import COUNTRIES
from video_library import TOPICS

def youtube(resource,**params):
    url='https://www.googleapis.com/youtube/v3/'+resource+'?'+urlencode(dict(key=os.environ['YOUTUBE_API_KEY'],**params))
    with urlopen(Request(url,headers={'User-Agent':'RumboLocal/1.0'}),timeout=12) as response:return json.loads(response.read(1000000))

def search(country,topic):
    if country not in COUNTRIES or topic not in TOPICS:raise ValueError()
    if not os.getenv('YOUTUBE_API_KEY'):raise ConnectionError('Configura YOUTUBE_API_KEY para buscar y verificar vídeos en todos los países.')
    matches=youtube('search',part='snippet',type='video',q=f'{COUNTRIES[country]} {TOPICS[topic]} español',relevanceLanguage='es',safeSearch='strict',videoEmbeddable='true',videoSyndicated='true',maxResults=8)
    ids=[x['id']['videoId'] for x in matches.get('items',[]) if 'videoId' in x.get('id',{})]
    if not ids:return []
    detail=youtube('videos',part='snippet,status,contentDetails',id=','.join(ids))
    result=[]
    for item in detail.get('items',[]):
        status=item.get('status',{})
        if status.get('privacyStatus')!='public' or not status.get('embeddable') or status.get('uploadStatus')!='processed':continue
        restrictions=item.get('contentDetails',{}).get('regionRestriction',{})
        if restrictions.get('allowed') or restrictions.get('blocked'):continue
        result.append(dict(title=item['snippet']['title'],country=country,topic=topic,url='https://www.youtube.com/watch?v='+item['id'],publisher=item['snippet']['channelTitle']))
    return result
