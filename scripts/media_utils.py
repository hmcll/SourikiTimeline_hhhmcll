import os
import json

from moviepy import VideoFileClip
from moviepy.config import FFMPEG_BINARY

from PIL import Image
from yt_dlp import YoutubeDL
from scripts.debug_utils import debug_args

@debug_args
def resize_image(input_image_path, output_image_path, size):
    original_image = Image.open(input_image_path)
    width, height = original_image.size
    aspect_ratio = width / height
    
    # ターゲットのサイズとアスペクト比を設定
    target_width = int(size[0])
    target_height = int(size[1])
    target_ratio = target_width / target_height

    if aspect_ratio > target_ratio:
        # 元の画像の方が横長
        new_width = target_width
        new_height = round(target_width / aspect_ratio)
    else:
        # 元の画像の方が縦長またはアスペクト比が等しい
        new_height = target_height
        new_width = round(target_height * aspect_ratio)
    
    resized_image = original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # 新しい画像を作成して黒で塗りつぶす
    new_image = Image.new("RGB", (target_width, target_height), "black")
    # リサイズした画像を新しい画像の中央に配置
    new_image.paste(resized_image, ((target_width - new_width) // 2, (target_height - new_height) // 2))

    # 画像を保存
    new_image.save(output_image_path, quality = 85)


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
        'ffmpeg_location': FFMPEG_BINARY,
    }
    with YoutubeDL(option) as ydl:
        result = ydl.download([url])
        if result != 0:
            raise Exception(f"ダウンロードに失敗しました。 url: {url}")


