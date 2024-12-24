from pytubefix import YouTube
from pytubefix.exceptions import RegexMatchError
from pytubefix.cli import on_progress
from flask import Flask, jsonify, request
from datetime import datetime
import os
import sys
import tempfile
import subprocess
import re
import argparse

app = Flask(__name__)
port = int(os.environ.get('PORT', 5000))
output_dir = None


@app.route('/')
def home():
    return 'Hello, this is a Flask Microservice for downloading YouTube videos!', 200


@app.route('/video_quality', methods=['GET'])
def get_mp4_streams():
    try:
        url = request.args.get('url')
        if not url:
            return 'No "url" passed as query parameter.', 400
        yt = YouTube(url)
        video_streams = yt.streams.filter(file_extension='mp4', adaptive=True,
                                            mime_type='video/mp4').order_by('resolution').desc()
        res = []
        for stream in video_streams:
            stream_data = {
                'itag': stream.itag,
                'type': stream.mime_type,
                'resolution': stream.resolution,
                'fps': stream.fps,
                'video_codec': stream.video_codec,
                'is_adaptive': stream.is_adaptive,
                'filesize_mb': round(stream.filesize_mb, 2),
                'height': stream.height,
                'width': stream.width,
                'includes_audio_track': stream.includes_audio_track,
                'includes_video_track': stream.includes_video_track
            }
            res.append(stream_data)
        return jsonify({'streams': res}), 200 if res else 204
    except RegexMatchError:
        return get_invalid_url_output(), 400
    except Exception as ex:
        return f'An error occured: {ex}.', 400


@app.route('/audio_quality', methods=['GET'])
def get_audio_streams():
    try:
        url = request.args.get('url')
        if not url:
            return 'No "url" passed as query parameter.', 400
        yt = YouTube(url)
        audio_streams = yt.streams.filter(only_audio=True,
                                            mime_type='audio/mp4').order_by('abr').desc()
        res = []
        for stream in audio_streams:
            stream_data = {
                'itag': stream.itag,
                'type': stream.mime_type,
                'abr': stream.abr,
                'audio_codec': stream.audio_codec,
                'is_adaptive': stream.is_adaptive,
                'filesize_mb': round(stream.filesize_mb, 2),
                'includes_audio_track': stream.includes_audio_track,
                'includes_video_track': stream.includes_video_track
            }
            res.append(stream_data)
        return jsonify({'streams': res}), 200 if res else 204
    except RegexMatchError:
        return get_invalid_url_output(), 400
    except Exception as ex:
        return f'An error occured: {ex}.', 400


@app.route('/title', methods=['GET'])
def get_title():
    try:
        url = request.args.get('url')
        if not url:
            return 'No "url" passed as query parameter.', 400
        yt = YouTube(url)
        return jsonify({'title': yt.title}), 200
    except RegexMatchError:
        return get_invalid_url_output(), 400
    except Exception as ex:
        return f'An error occured: {ex}.', 400


@app.route('/download_mp4', methods=['POST'])
def download_mp4():
    if not is_ffmpeg_installed_helper():
        return 'ffmpeg is not installed, aborting download operation. Please ensure ffmpeg is installed.', 400
    try:
        json_data = request.get_json(force=True)
        if 'url' not in json_data:
            return 'No "url" passed in request body.', 400
        if 'video_itag' not in json_data:
            return 'No "video_itag" passed in request body.', 400
        if 'audio_itag' not in json_data:
            return 'No "audio_itag" passed in request body.', 400
        url = json_data['url']
        yt = YouTube(url, on_progress_callback=on_progress)
        video_itag = json_data['video_itag']
        video_stream = yt.streams.filter(file_extension='mp4', adaptive=True,
                                         mime_type='video/mp4').order_by('resolution').desc().get_by_itag(video_itag)
        if not video_stream:
            return 'Invalid "video_itag" passed.', 400
        audio_itag = json_data['audio_itag']
        audio_stream = yt.streams.filter(only_audio=True,
                                         mime_type='audio/mp4').order_by('abr').desc().get_by_itag(audio_itag)
        if not audio_stream:
            return 'Invalid "audio_itag" passed.', 400
        tmp_dir = tempfile.TemporaryDirectory(prefix='youtube-dl-tmp-', dir=os.getcwd())
        start = datetime.now()
        video_stream.download(output_path=tmp_dir.name, filename='video.mp4')
        print('\nVideo stream download complete.')
        end = datetime.now()
        video_download_total_seconds = (end - start).total_seconds()
        start = datetime.now()
        audio_stream.download(output_path=tmp_dir.name, filename='audio.mp4')
        print('\nAudio stream download complete.')
        end = datetime.now()
        audio_download_total_seconds = (end - start).total_seconds()
        video_path = os.path.join(tmp_dir.name, 'video.mp4')
        audio_path = os.path.join(tmp_dir.name, 'audio.mp4')
        clean_title = get_clean_video_title(yt.title)
        output_path = os.path.join(output_dir, f'{clean_title}.mp4')
        cmd = f'ffmpeg -y -loglevel quiet -i {video_path} -i {audio_path} -c:v copy -c:a copy {output_path}'
        start = datetime.now()
        subprocess.run(cmd, shell=True)
        end = datetime.now()
        tmp_dir.cleanup()
        merge_total_seconds = (end - start).total_seconds()
        total_seconds = video_download_total_seconds + audio_download_total_seconds + merge_total_seconds
        res = {
            'file_name': f'{clean_title}.mp4',
            'file_location': output_dir if sys.platform != 'win32' else output_dir.replace('\\', '/'),
            'filesize_mb': round(os.path.getsize(output_path) / (1024 ** 2), 2),
            'video_download_total_seconds': float(f'{video_download_total_seconds:.03f}'),
            'audio_download_total_seconds': float(f'{audio_download_total_seconds:.03f}'),
            'merge_total_seconds': float(f'{merge_total_seconds:.03f}'),
            'total_seconds_elasped': float(f'{total_seconds:.03f}'),
            'video_title': yt.title,
            'height': video_stream.height,
            'width': video_stream.width,
            'video_stream_download_size_mb': round(video_stream.filesize_mb, 2),
            'audio_stream_download_size_mb': round(audio_stream.filesize_mb, 2),
            'resolution': video_stream.resolution,
            'fps': video_stream.fps,
            'includes_audio_track': audio_stream.includes_audio_track,
            'includes_video_track': video_stream.includes_video_track
        }
        return jsonify(res), 200
    except RegexMatchError:
        return get_invalid_url_output(), 400
    except Exception as ex:
        return f'An error occured: {ex}.', 400
    

@app.route('/download_mp3', methods=['POST'])
def download_mp3():
    if not is_ffmpeg_installed_helper():
        return 'ffmpeg is not installed, aborting download operation. Please ensure ffmpeg is installed.', 400
    try:
        json_data = request.get_json(force=True)
        if 'url' not in json_data:
            return 'No "url" passed in request body.', 400
        if 'audio_itag' not in json_data:
            return 'No "audio_itag" passed in request body.', 400
        url = json_data['url']
        yt = YouTube(url, on_progress_callback=on_progress)
        audio_itag = json_data['audio_itag']
        audio_stream = yt.streams.filter(only_audio=True,
                                            mime_type='audio/mp4').order_by('abr').desc().get_by_itag(audio_itag)
        if not audio_stream:
            return 'Invalid "audio_itag" passed.', 400
        tmp_dir = tempfile.TemporaryDirectory(prefix='youtube-dl-tmp-', dir=os.getcwd())
        start = datetime.now()
        audio_stream.download(output_path=tmp_dir.name, filename='audio.mp4')
        print('\nAudio stream download complete.')
        end = datetime.now()
        download_total_seconds = (end - start).total_seconds()
        mp4_path = os.path.join(tmp_dir.name, 'audio.mp4')
        clean_title = get_clean_video_title(yt.title)
        mp3_path = os.path.join(output_dir, f'{clean_title}.mp3')
        start = datetime.now()
        subprocess.run(f'ffmpeg -y -loglevel quiet -i {mp4_path} -f mp3 -ab 320000 -vn {mp3_path}',
                       shell=True)
        end = datetime.now()
        tmp_dir.cleanup()
        convert_total_seconds = (end - start).total_seconds()
        total_seconds = convert_total_seconds + download_total_seconds
        res = {
            'file_name': f'{clean_title}.mp3',
            'file_location': output_dir if sys.platform != 'win32' else output_dir.replace('\\', '/'),
            'filesize_mb': round(os.path.getsize(mp3_path) / (1024 ** 2), 2),
            'audio_download_total_seconds': float(f'{download_total_seconds:.03f}'),
            'convert_total_seconds': float(f'{convert_total_seconds:.03f}'),
            'total_seconds_elasped': float(f'{total_seconds:.03f}'),
            'video_title': yt.title,
            'audio_stream_download_size_mb': round(audio_stream.filesize_mb, 2),
            'abr': audio_stream.abr,
            'includes_audio_track': audio_stream.includes_audio_track,
            'includes_video_track': audio_stream.includes_video_track
        }
        return jsonify(res), 200
    except RegexMatchError:
        return get_invalid_url_output(), 400
    except Exception as ex:
        return f'An error occured: {ex}.', 400


@app.route('/thumbnail', methods=['GET'])
def get_thumbnail():
    try:
        url = request.args.get('url')
        if not url:
            return 'No "url" passed as query parameter.', 400
        yt = YouTube(url)
        return jsonify({'thumbnail_url': yt.thumbnail_url}), 200
    except RegexMatchError:
        return get_invalid_url_output(), 400
    except Exception as ex:
        return f'An error occured: {ex}.', 400


@app.route('/video_info', methods=['GET'])
def get_video_info():
    try:
        url = request.args.get('url')
        if not url:
            return 'No "url" passed as query parameter.', 400
        yt = YouTube(url)
        res = {
            'title': yt.title,
            'author': yt.author,
            'channel_id': yt.channel_id,
            'channel_url': yt.channel_url,
            'description': yt.description,
            'video_id': yt.video_id,
            'video_url': f'https://youtube.com/watch?v={yt.video_id}',
            'length_in_minutes': round(yt.length / 60, 2),
            'likes': int(yt.likes) if yt.likes else yt.likes,
            'publish_date': yt.publish_date,
            'rating': yt.rating,
            'views': yt.views,
            'keywords': yt.keywords,
            'thumbnail_url': yt.thumbnail_url
        }
        return jsonify(res), 200
    except RegexMatchError:
        return get_invalid_url_output(), 400
    except Exception as ex:
        return f'An error occured: {ex}.', 400
    

@app.route('/is_ffmpeg_installed', methods=['GET'])
def is_ffmpeg_installed():
    return jsonify(is_ffmpeg_installed_helper()), 200


@app.route('/output_directory_path', methods=['GET'])
def get_output_directory_path():
    return jsonify({'output_directory_path': output_dir if sys.platform != 'win32' else output_dir.replace('\\', '/')}), 200


def get_invalid_url_output():
    p1 = r'https://youtube.com/watch?v={video_id}'
    p2 = r'https://youtube.com/embed/{video_id}'
    p3 = r'https://youtu.be/{video_id}'
    return f'Invalid "url" and/or video_id passed. This API supports the following YouTube url patterns: "{p1}", "{p2}", and "{p3}".'


def is_ffmpeg_installed_helper():
    try:
        res = subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, text=True)
        version_line = res.stdout.splitlines()[0]
        version = version_line.split(' ')[2]
        return True
    except Exception:
        return False


def get_clean_video_title(video_title):
    # Remove invalid characters for filenames
    res = re.sub(r'[\/:*?"<>|]', '', video_title)
    # Trim and replace spaces with underscores
    res = res.strip().replace(' ', '_')
    # Ensure the filename is not too long
    max_filename_length = 255  # Maximum length for most file systems
    if len(res) > max_filename_length:
        res = res[:max_filename_length]
    return res


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-dest', '--destination', default='.', type=str, help='destination directory (absolute path) to download output files (not streams) to, defaults to current directory')
    args = parser.parse_args()
    print(f'Destination directory: {os.path.abspath(args.destination)}')
    output_dir = os.path.abspath(args.destination)
    app.run(debug=True, port=port)