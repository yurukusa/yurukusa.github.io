"""Fetch the most recent open bug issues from anthropics/claude-code.
Run via cron or GitHub Actions to keep ai-incident-watch/data.json fresh.
"""
import datetime
import json
import subprocess
import sys
from pathlib import Path
REPO = 'anthropics/claude-code'
PER_PAGE = 50
OUT_PATH = Path(__file__).resolve().parent.parent / 'ai-incident-watch' / 'data.json'
def fetch_issues() -> list:
    args = [
        'gh', 'api', '-X', 'GET',
        f'repos/{REPO}/issues',
        '-f', 'state=open',
        '-f', 'labels=bug',
        '-f', 'sort=created',
        '-f', 'direction=desc',
        '-f', f'per_page={PER_PAGE}',
    ]
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        print(f'gh api failed: {result.stderr}', file=sys.stderr)
        sys.exit(1)
    return json.loads(result.stdout)
def shape(issue: dict) -> dict:
    labels = [l['name'] for l in issue.get('labels', [])]
    return {
        'number': issue['number'],
        'title': issue['title'],
        'created_at': issue['created_at'],
        'updated_at': issue['updated_at'],
        'labels': labels,
        'comments': issue.get('comments', 0),
        'reactions': issue.get('reactions', {}).get('total_count', 0),
        'url': issue['html_url'],
        'has_repro': 'has repro' in labels,
        'is_regression': 'regression' in labels,
    }
def main() -> None:
    issues = fetch_issues()
    items = [shape(i) for i in issues if not i.get('pull_request')]
    payload = {
        'generated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'count': len(items),
        'source': f'github.com/{REPO} (open bug issues, sorted by created)',
        'items': items,
    }
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Saved {len(items)} items to {OUT_PATH.relative_to(OUT_PATH.parent.parent)}')
if __name__ == '__main__':
    main()
