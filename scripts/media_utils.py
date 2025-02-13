import os
import json

from yt_dlp import YoutubeDL



def get_video_info(url):
    
    ydl_opts = {}
    with YoutubeDL(ydl_opts) as ydl:
        
        info = ydl.extract_info(url, download=False)
        jsonRet = json.loads(json.dumps(ydl.sanitize_info(info)))
        title = jsonRet['title']
        
        
    return title, jsonRet

def ydl_download(url, output_path):
    if os.path.exists(output_path):
        os.remove(output_path)
    
    option = {
        'outtmpl': output_path,
        'format': "bestvideo[ext=mp4]/best",
    }
    with YoutubeDL(option) as ydl:
        result = ydl.download([url])
        if result != 0:
            raise Exception(f"ダウンロードに失敗しました。 url: {url}")


