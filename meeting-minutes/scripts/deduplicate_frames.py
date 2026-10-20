#!/usr/bin/env python3
"""Conservative, local screenshot deduplication; originals are never changed."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image


def features(path, roi):
    with Image.open(path) as im:
        w, h = im.size
        region = im.convert('RGB').crop(tuple(round(v * (w if i % 2 == 0 else h)) for i, v in enumerate(roi)))
        rgb = np.asarray(region.resize((256, 144), Image.Resampling.LANCZOS), dtype=np.float32) / 255
        gray = np.asarray(region.convert('L').resize((32, 32), Image.Resampling.LANCZOS), dtype=np.float32)
    n = np.arange(32)
    basis = np.cos(np.pi / 32 * (n[None, :] + .5) * np.arange(8)[:, None])
    low = (basis @ gray @ basis.T).ravel()[1:]
    bits = low > np.median(low)
    lum = rgb.mean(axis=2).reshape(18, 8, 32, 8).transpose(0, 2, 1, 3).reshape(-1, 64)
    return rgb, bits, lum


def compare(a, b):
    mae = float(np.abs(a[0] - b[0]).mean())
    distance = int(np.count_nonzero(a[1] != b[1]))
    x, y = a[2], b[2]
    mx, my = x.mean(1), y.mean(1)
    vx, vy = x.var(1), y.var(1)
    covariance = ((x - mx[:, None]) * (y - my[:, None])).mean(1)
    ssim = float(np.mean(((2 * mx * my + .0001) * (2 * covariance + .0009)) /
                         ((mx * mx + my * my + .0001) * (vx + vy + .0009))))
    return {'mae': round(mae, 6), 'phash_distance': distance, 'ssim': round(ssim, 6)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('manifest', type=Path, help='JSON with frames; paths relative to manifest directory')
    p.add_argument('output', type=Path, help='New directory; refuses overwrite')
    p.add_argument('--mae', type=float, default=.025)
    p.add_argument('--ssim', type=float, default=.94)
    p.add_argument('--phash', type=int, default=10)
    a = p.parse_args()
    if not (0 <= a.mae <= 1 and 0 <= a.ssim <= 1 and 0 <= a.phash <= 63):
        p.error('Invalid similarity thresholds')
    manifest = a.manifest.resolve(strict=True)
    raw = json.loads(manifest.read_text())
    rows = raw['frames']
    if not rows:
        p.error('No frames')
    a.output.mkdir(parents=False, exist_ok=False)
    (a.output / 'frames').mkdir()
    selected, groups, decisions = [], {}, []
    for index, row in enumerate(rows):
        path = (manifest.parent / row['file']).resolve(strict=True)
        if not path.is_relative_to(manifest.parent):
            raise ValueError('Frame must be inside the manifest directory')
        roi = row.get('compare_roi', [0, 0, 1, 1])
        if len(roi) != 4 or not (0 <= roi[0] < roi[2] <= 1 and 0 <= roi[1] < roi[3] <= 1):
            raise ValueError('Invalid normalized ROI')
        group = (row.get('group', 'default'), tuple(roi))
        f = features(path, roi)
        duplicate = None
        for old, old_feature in groups.get(group, []):
            metrics = compare(f, old_feature)
            same_key = bool(row.get('content_key')) and row.get('content_key') == old.get('content_key')
            if same_key or (not row.get('content_key') and metrics['mae'] <= a.mae and metrics['ssim'] >= a.ssim and metrics['phash_distance'] <= a.phash):
                duplicate = {'kept_id': old['id'], **metrics}
                break
        item = dict(row, id=row.get('id', f'F{index + 1:04}'))
        if duplicate:
            decisions.append({'id': item['id'], 'file': row['file'], 'status': 'duplicate', **duplicate})
            continue
        target = a.output / 'frames' / f'{len(selected) + 1:03}_{path.name}'
        shutil.copyfile(path, target)
        item['source_file'] = row['file']
        item['file'] = str(target.relative_to(a.output))
        item['sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
        selected.append(item)
        groups.setdefault(group, []).append((item, f))
        decisions.append({'id': item['id'], 'file': row['file'], 'status': 'kept'})
    result = {'input_count': len(rows), 'retained_count': len(selected), 'duplicate_count': len(rows) - len(selected),
              'thresholds': {'mae_max': a.mae, 'ssim_min': a.ssim, 'phash_max': a.phash},
              'method': 'Compare only the specified ROI within each group; retain full original frame bytes. Conservative visual similarity, not semantic proof.',
              'frames': selected, 'decisions': decisions}
    (a.output / 'deduplication.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps({k: result[k] for k in ['input_count', 'retained_count', 'duplicate_count']}))


if __name__ == '__main__':
    main()
