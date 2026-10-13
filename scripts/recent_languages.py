"""Render a dated language estimate using only explicitly public repositories."""
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from html import escape
import json
from pathlib import Path
import subprocess


def github(path, *fields):
    """Read GitHub JSON with gh's existing authentication, without exposing tokens."""
    result = subprocess.run(['gh', 'api', '-X', 'GET', path, *fields], check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def generate():
    """Weight each public repository's language proportions by recent authored commits."""
    today = datetime.now(timezone.utc).date()
    since = (today - timedelta(days=90)).isoformat()
    repos = github('search/repositories', '-f', f'q=user:imddc is:public pushed:>={since}', '-f', 'per_page=100')
    if repos['total_count'] > 100:
        raise RuntimeError('Repository sample exceeds 100; add pagination before publishing.')
    scores = defaultdict(float)
    commit_total = 0
    for repo in repos['items']:
        if repo['private'] or repo['fork'] or repo['archived']:
            continue
        name = repo['full_name']
        commits = []
        for page in range(1, 101):
            batch = github(f'repos/{name}/commits', '-f', 'author=imddc', '-f', f'since={since}T00:00:00Z', '-f', 'per_page=100', '-f', f'page={page}')
            commits.extend(batch)
            if len(batch) < 100:
                break
        else:
            raise RuntimeError('Commit sample exceeds pagination limit.')
        languages = github(f'repos/{name}/languages')
        total = sum(languages.values())
        if not total:
            continue
        commit_total += len(commits)
        for language, size in languages.items():
            scores[language] += len(commits) * size / total
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:6]
    palette = ['#9dccff', '#9de5d4', '#d2b8ff', '#ffd09d', '#f2accb', '#b7c5dd']
    all_score = sum(scores.values())
    rows = []
    for index, (language, score) in enumerate(ranked):
        percent = score / all_score * 100 if all_score else 0
        y = 128 + index * 53
        color = palette[index]
        rows.append(f'<text x="36" y="{y}" fill="#e4eef9" font-size="16">{index+1:02}  {escape(language)}</text><text x="764" y="{y}" text-anchor="end" fill="{color}" font-size="14">{percent:.1f}%</text><rect x="36" y="{y+12}" width="728" height="4" rx="2" fill="#24364d"/><rect x="36" y="{y+12}" width="{728*percent/100:.2f}" height="4" rx="2" fill="{color}"/>')
    height = 160 + max(len(ranked), 1) * 53
    empty = '<text x="36" y="140" fill="#93adc7">No public activity in this period.</text>' if not ranked else ''
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="{height}" viewBox="0 0 800 {height}" role="img" aria-labelledby="title desc"><title id="title">Recent public language activity</title><desc id="desc">90-day estimate weighted by authored commits and repository language bytes, updated {today}.</desc><rect width="800" height="{height}" rx="18" fill="#0c1729"/><g font-family="Arial, sans-serif"><text x="36" y="42" fill="#a5d3ff" font-size="11" letter-spacing="3">RECENT / 90 DAYS</text><text x="36" y="78" fill="#f1f6ff" font-size="27" font-weight="700">Languages in motion.</text><text x="764" y="42" fill="#829ab5" font-size="11" text-anchor="end">UPDATED {today}</text>{''.join(rows)}{empty}<text x="36" y="{height-22}" fill="#829ab5" font-size="11">PUBLIC REPOS · COMMIT-WEIGHTED ESTIMATE · NOT CODING TIME</text></g></svg>'''
    Path('assets/recent-languages.svg').write_text(svg)
    Path('assets/recent-languages.json').write_text(json.dumps({'updated':str(today),'since':since,'publicAuthoredCommits':commit_total,'method':'Authored commits multiplied by repository language-byte proportions. Public non-fork personal repositories only; not coding time or changed-line language.','languages':[{'name':name,'percent':round(score/all_score*100,1)} for name,score in ranked]}, indent=2)+'\n')
    print(f'Generated {len(ranked)} languages from {commit_total} authored public commits; {since} to {today}.')


if __name__ == '__main__':
    generate()
