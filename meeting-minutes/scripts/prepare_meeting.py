#!/usr/bin/env python3
"""Local, non-destructive meeting evidence preparation. Python 3.9+, ffmpeg/ffprobe."""
import argparse
import concurrent.futures
import hashlib
import html
import json
import subprocess
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


def run(args):
    return subprocess.run(args, check=True, capture_output=True).stdout


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def timestamp(t):
    t = int(t)
    return f'{t // 3600:02}:{t // 60 % 60:02}:{t % 60:02}'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--video', required=True, type=Path)
    p.add_argument('--notes', type=Path, help='DOCX or UTF-8 text/Markdown')
    p.add_argument('--output', required=True, type=Path, help='New directory; refuses overwrite')
    p.add_argument('--interval', type=float, default=30, help='Full-frame sampling interval in seconds')
    p.add_argument('--workers', type=int, default=3)
    p.add_argument('--extra-times', default='', help='Additional comma-separated seconds')
    p.add_argument('--skip-audio', action='store_true')
    a = p.parse_args()
    if a.interval <= 0 or a.workers < 1:
        p.error('interval and workers must be positive')
    video = a.video.resolve(strict=True)
    notes = a.notes.resolve(strict=True) if a.notes else None
    probe = json.loads(run(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(video)]))
    duration = float(probe['format']['duration'])
    extra = [float(x) for x in a.extra_times.split(',') if x.strip()]
    if any(t < 0 or t >= duration for t in extra):
        p.error('extra timestamps must be within the video duration')
    out = a.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    frames = out / 'frames'
    frames.mkdir()
    sources = [{'path': str(video), 'sha256': sha256(video), 'bytes': video.stat().st_size}]
    (out / 'video-probe.json').write_text(json.dumps(probe, ensure_ascii=False, indent=2))
    if notes:
        sources.append({'path': str(notes), 'sha256': sha256(notes), 'bytes': notes.stat().st_size})
        if notes.suffix.lower() == '.docx':
            ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            with zipfile.ZipFile(notes) as z:
                root = ET.fromstring(z.read('word/document.xml'))
                paragraphs = []
                for el in root.findall('.//w:body//w:p', ns):
                    text = ''.join(t.text or '' for t in el.findall('.//w:t', ns))
                    if text.strip():
                        paragraphs.append({'id': f'P{len(paragraphs)+1:03}', 'text': text})
                (out / 'notes.json').write_text(json.dumps(paragraphs, ensure_ascii=False, indent=2))
                (out / 'notes.txt').write_text('\n'.join(f"[{x['id']}] {x['text']}" for x in paragraphs))
                media = out / 'notes-media'
                media.mkdir()
                for name in z.namelist():
                    if name.startswith('word/media/') and not name.endswith('/'):
                        # Flatten paths; never extract arbitrary ZIP entries.
                        (media / Path(name).name).write_bytes(z.read(name))
        else:
            (out / 'notes.txt').write_text(notes.read_text(encoding='utf-8'))
    if not a.skip_audio and any(s['codec_type'] == 'audio' for s in probe['streams']):
        run(['ffmpeg', '-nostdin', '-v', 'error', '-n', '-i', str(video), '-map', '0:a:0', '-vn', '-ar', '16000', '-ac', '1', '-c:a', 'pcm_s16le', str(out / 'audio-16k.wav')])
    times = {round(i * a.interval, 3) for i in range(int(duration // a.interval) + 1) if i * a.interval < duration}
    times.update(round(t, 3) for t in extra)
    times.add(round(max(0, duration - 1), 3))
    def extract(item):
        i, t = item
        name = f'F{i:03}_{int(t//3600):02}-{int(t//60%60):02}-{int(t%60):02}.jpg'
        path = frames / name
        run(['ffmpeg', '-nostdin', '-v', 'error', '-threads', '1', '-ss', str(t), '-i', str(video), '-frames:v', '1', '-q:v', '2', '-n', str(path)])
        return {'id': f'F{i:03}', 'seconds': t, 'timestamp': timestamp(t), 'file': f'frames/{name}', 'sha256': sha256(path)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as ex:
        entries = list(ex.map(extract, enumerate(sorted(times), 1)))
    audio_stream = next((s for s in probe['streams'] if s['codec_type'] == 'audio'), None)
    audio_offset = float(audio_stream.get('start_time', 0)) - float(probe['format'].get('start_time', 0)) if audio_stream else None
    manifest = {'sources': sources, 'duration_seconds': duration, 'sampling_interval_seconds': a.interval, 'audio_timing': {'wav_seconds_to_recording_seconds_offset': audio_offset, 'note': 'Add this offset to ASR times from the extracted WAV when citing recording timestamps; verify sync for discontinuous media.'}, 'coverage': 'full-frame interval samples plus requested extra timestamps; not every frame or every transient slide', 'frames': entries}
    (out / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    cards = ''.join(f'<figure><a href="{html.escape(x["file"])}"><img loading="lazy" src="{html.escape(x["file"])}"></a><figcaption>{x["id"]} · {x["timestamp"]} · 点击查看原分辨率全画面</figcaption></figure>' for x in entries)
    (out / '截图附录.html').write_text('<!doctype html><html lang="zh"><meta charset="utf-8"><title>会议录屏完整画面截图附录</title><style>body{max-width:1600px;margin:30px auto;font-family:system-ui;background:#f4f4f2;color:#172b3a}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(550px,1fr));gap:20px}figure{margin:0;background:white;padding:10px}img{width:100%;height:auto}figcaption{padding:10px}a{color:inherit}@media(max-width:600px){main{display:block}figure{margin-bottom:15px}}@media print{main{display:block}figure{break-inside:avoid}body{background:white}}</style><h1>完整画面截图附录</h1><p>原始画面，不裁切分享内容或人物；源画面未显示的人物不补造。全程每 '+str(a.interval)+' 秒抽样并保留尾帧，共 '+str(len(entries))+' 张；这是全程抽样，不是逐帧或全部短暂页面的保证。仅供内部复核。</p><main>'+cards+'</main></html>', encoding='utf-8')
    print(json.dumps({'output':str(out), 'duration':duration,'frames':len(entries),'sources':sources},ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
