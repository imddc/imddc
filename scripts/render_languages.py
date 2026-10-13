"""Render language assets in the profile's shared visual palette."""
from html import escape


def render_languages(languages, updated):
    """Draw a compact ranking with a dated public-activity label."""
    palette = ['#c6f56d', '#bba5ff', '#a0d9ec', '#f2c58d', '#eaa3bd', '#a0b3a9']
    rows = []
    offset = 36.0
    for index, item in enumerate(languages):
        value = item['percent']
        color = palette[index % len(palette)]
        width = 728 * value / 100
        rows.append(f'<rect x="{offset:.2f}" y="91" width="{width:.2f}" height="8" fill="{color}"/>')
        offset += width
        x = 36 + (index % 2) * 380
        y = 144 + (index // 2) * 69
        rows.append(f'<text x="{x}" y="{y}" fill="#6c7971" font-size="10">0{index+1}</text><text x="{x+27}" y="{y}" fill="#ecf0e8" font-size="20" font-weight="600">{escape(item["name"])}</text><text x="{x+345}" y="{y}" text-anchor="end" fill="{color}" font-size="12">{value:.1f}%</text><path d="M{x} {y+20}h345" stroke="#ffffff" stroke-opacity=".09"/>')
    height = 171 + max(1, (len(languages)+1)//2) * 69
    if not languages:
        rows.append('<text x="36" y="146" fill="#9aa79e" font-size="15">No recent public activity.</text>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="{height}" viewBox="0 0 800 {height}" role="img" aria-label="Recent language activity estimate"><rect width="800" height="{height}" rx="12" fill="#11161b"/><g font-family="Arial, sans-serif"><text x="36" y="31" fill="#9ba59e" font-size="9" letter-spacing="3">RECENT LANGUAGES / 90 DAYS</text><text x="36" y="67" fill="#edf0e8" font-size="25" font-weight="600">Code in motion.</text><text x="764" y="31" text-anchor="end" fill="#78867c" font-size="9">{escape(updated)}</text>{''.join(rows)}<text x="36" y="{height-23}" fill="#7d8c81" font-size="9" letter-spacing="1.3">PUBLIC ACTIVITY / ESTIMATED</text><text x="764" y="{height-23}" text-anchor="end" fill="#c6f56d" font-size="12">↗</text></g></svg>'''
