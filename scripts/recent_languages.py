"""Render a dated language estimate using only explicitly public repositories."""
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from render_languages import render_languages
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
    all_score = sum(scores.values())
    language_data = [{'name':name,'percent':round(score/all_score*100,1)} for name,score in ranked]
    Path('assets/recent-languages.svg').write_text(render_languages(language_data, str(today)))
    Path('assets/recent-languages.json').write_text(json.dumps({'updated':str(today),'since':since,'publicAuthoredCommits':commit_total,'method':'Authored commits multiplied by repository language-byte proportions. Public non-fork personal repositories only; not coding time or changed-line language.','languages':[{'name':name,'percent':round(score/all_score*100,1)} for name,score in ranked]}, indent=2)+'\n')
    print(f'Generated {len(ranked)} languages from {commit_total} authored public commits; {since} to {today}.')


if __name__ == '__main__':
    generate()
