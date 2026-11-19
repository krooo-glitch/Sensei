#!/usr/bin/env python3
"""Publish the approved message on December 1, 2026, after 08:00 JST only."""
import argparse
from datetime import datetime, time
import json
from pathlib import Path
import subprocess
from zoneinfo import ZoneInfo

parser = argparse.ArgumentParser()
parser.add_argument('--dry-run', action='store_true')
parser.add_argument('--now', help='ISO timestamp, allowed only with --dry-run for tests')
args = parser.parse_args()
if args.now and not args.dry_run:
    parser.error('--now is allowed only with --dry-run')
now = datetime.fromisoformat(args.now) if args.now else datetime.now(ZoneInfo('Asia/Tokyo'))
if now.tzinfo is None:
    parser.error('--now must have an explicit timezone')
now = now.astimezone(ZoneInfo('Asia/Tokyo'))
if now.date().isoformat() != '2026-12-01' or now.time() < time(8, 0):
    print('DATE_GUARD: no publication at ' + now.isoformat())
    raise SystemExit(0)
root = Path(__file__).resolve().parents[1]
staged = root / 'scheduled' / '2026-12.json'
live = root / 'Sensei' / 'monkly_messages.json'
message = json.loads(staged.read_text(encoding='utf-8'))
assert len(message) == 1
m = message[0]
assert set(m) == {'id', 'date', 'monthYear', 'title', 'body', 'signoff'}
assert m['id'] == '2026-12' and m['date'] == '2026-12-01'
assert m['monthYear'] == 'December 2026'
assert m['title'] == 'When the Day Draws to a Close'
assert m['signoff'] == 'Koji'
assert m['body'].startswith('Dear friend,') and 'Shandao' in m['body']
current = json.loads(live.read_text(encoding='utf-8'))
assert len(current) == 1
if current == message:
    print('ALREADY_PUBLISHED: no duplicate commit')
    raise SystemExit(0)
if current[0]['date'] >= m['date']:
    print('NO_ROLLBACK: current message is not older than December')
    raise SystemExit(0)
if args.dry_run:
    print('DRY_RUN: validated December message; live feed unchanged')
    raise SystemExit(0)
live.write_text(json.dumps(message, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
assert json.loads(live.read_text(encoding='utf-8')) == message
for command in (
    ['git', 'diff', '--check'],
    ['git', 'config', 'user.name', 'github-actions[bot]'],
    ['git', 'config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com'],
    ['git', 'add', 'Sensei/monkly_messages.json'],
    ['git', 'commit', '-m', 'Publish December 2026 Sensei message'],
    ['git', 'push', 'origin', 'HEAD:main'],
):
    subprocess.run(command, cwd=root, check=True)
print('PUBLISHED: December 2026 message')
