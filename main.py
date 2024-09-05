from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

def fetch_video_info(url):
    ydl_opts = {
        'quiet': True,
        'format': 'bestvideo+bestaudio/best',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
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

            # Filter formats
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
            return {'error': str(e)}

@app.route('/',methods=["GET"])
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
