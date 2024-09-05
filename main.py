from flask import Flask, request, jsonify
import yt_dlp
import os
import json

app = Flask(__name__)

# Path to where your OAuth2 token data is stored
TOKEN_CACHE_PATH = os.path.expanduser("./token_data.json")

def fetch_video_info(url):
    # Check if the token data exists
    if not os.path.exists(TOKEN_CACHE_PATH):
        return {'error': 'OAuth2 token data not found. Please authorize yt-dlp locally first.'}

    # Load the OAuth2 token data
    with open(TOKEN_CACHE_PATH, 'r') as token_file:
        token_data = json.load(token_file)
    print("Loaded token data:", token_data)

    ydl_opts = {
        'quiet': True,
        'format': 'bestvideo+bestaudio/best',
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        },
        'username': 'oauth2',
        'password': '',
        'cachedir': os.path.dirname(TOKEN_CACHE_PATH),
        'token_data': token_data,
        'verbose': True
    }
    print("Starting yt-dlp with options:", ydl_opts)
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            print("Extracting video info...")
            info = ydl.extract_info(url, download=False)
            print("Video info extracted:", info)

            formats = []
            for format in info['formats']:
                has_video = 'vcodec' in format and format['vcodec'] != 'none'
                is_60fps = format.get('fps') == 60

                formats.append({
                    'itag': format.get('format_id'),
                    'qualityLabel': format.get('format_note', 'Audio only'),
                    'container': format.get('ext', 'unknown'),
                    'size': f"{round(int(format.get('filesize', 0)) / (1024 * 1024), 2)} MB" if format.get('filesize') else 'N/A',
                    'type': 'video' if has_video else 'audio',
                    'is60fps': is_60fps,
                    'url': format.get('url'),
                    'vcodec': format.get('vcodec', 'none'),
                    'acodec': format.get('acodec', 'none'),
                })

            filtered_formats = [
                fmt for fmt in formats
                if fmt['size'] != 'N/A' and fmt['container'] not in ['mhtml']
            ]

            return {
                'title': info.get('title'),
                'thumbnail': info.get('thumbnail', ''),
                'formats': filtered_formats,
            }
        except Exception as e:
            print("Exception occurred:", e)
            return {'error': str(e)}

@app.route('/', methods=["GET"])
def welcome():
    return "Welcome to the YouTube Downloader API!"

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({'error': 'URL is required'}), 400

    video_info = fetch_video_info(url)

    if 'error' in video_info:
        return jsonify(video_info), 500

    return jsonify(video_info)

if __name__ == '__main__':
    app.run(debug=True)
