#!/usr/bin/env python3
"""Offline ASR with an existing faster-whisper model; requires 16 kHz mono PCM WAV."""
import argparse
import json
import os
import time
import wave
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('audio', type=Path)
    p.add_argument('output', type=Path, help='New directory; refuses overwrite')
    p.add_argument('--model', required=True, type=Path, help='Existing local CTranslate2 model directory')
    p.add_argument('--language', default='zh')
    p.add_argument('--threads', type=int, default=6)
    a = p.parse_args()
    audio_path = a.audio.resolve(strict=True)
    model_path = a.model.resolve(strict=True)
    if not model_path.is_dir() or a.threads < 1:
        p.error('model must be a directory; threads must be positive')
    os.environ['HF_HUB_OFFLINE'] = '1'
    from faster_whisper import WhisperModel
    import numpy as np
    with wave.open(str(audio_path), 'rb') as wav:
        if (wav.getframerate(), wav.getnchannels(), wav.getsampwidth()) != (16000, 1, 2):
            p.error('Input must be mono 16-bit 16 kHz PCM; use prepare_meeting.py')
        audio = np.frombuffer(wav.readframes(wav.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    a.output.mkdir(parents=True, exist_ok=False)
    started = time.time()
    model = WhisperModel(str(model_path), device='cpu', compute_type='int8', cpu_threads=a.threads, local_files_only=True)
    segments, info = model.transcribe(audio, language=a.language, beam_size=5, vad_filter=True, condition_on_previous_text=False)
    rows = []
    def ts(t, sep='.'):
        ms = round(t * 1000)
        return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02}{sep}{ms%1000:03}'
    with (a.output/'transcript.jsonl').open('x', encoding='utf-8') as j, (a.output/'transcript.txt').open('x', encoding='utf-8') as txt, (a.output/'transcript.srt').open('x', encoding='utf-8') as srt:
        for i, s in enumerate(segments, 1):
            row = {'id': f'T{i:04}', 'start': s.start, 'end': s.end, 'text': s.text, 'avg_logprob': s.avg_logprob, 'no_speech_prob': s.no_speech_prob}
            rows.append(row)
            j.write(json.dumps(row, ensure_ascii=False)+'\n'); j.flush()
            txt.write(f'[{row["id"]} {ts(s.start)}–{ts(s.end)}] {s.text}\n'); txt.flush()
            srt.write(f'{i}\n{ts(s.start, ",")} --> {ts(s.end, ",")}\n{s.text}\n\n'); srt.flush()
            if i % 20 == 0:
                print(f'segments={i} position={ts(s.end)}', flush=True)
    result = {'engine': 'faster-whisper', 'model': str(model_path), 'language': info.language, 'duration': info.duration, 'elapsed_seconds': round(time.time()-started, 2), 'review_status': 'ASR raw; not verbatim verified; no speaker identity', 'segments': rows}
    (a.output/'transcript.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'complete segments={len(rows)} elapsed={result["elapsed_seconds"]}s')


if __name__ == '__main__':
    main()
