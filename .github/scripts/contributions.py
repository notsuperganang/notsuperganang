"""Render the GitHub contribution calendar as a grey SVG (asset/contributions.svg).

Usage: GITHUB_TOKEN=... python contributions.py <login> <out.svg>
"""

import json
import os
import sys
import urllib.request
from datetime import date

QUERY = """query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date weekday contributionLevel } }
      }
    }
  }
}"""

LEVELS = ["NONE", "FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE"]
CELL, GAP, LEFT, TOP = 11, 3, 32, 20
STEP = CELL + GAP

# Greys for light and dark GitHub themes; picked by prefers-color-scheme inside the SVG
STYLE = """
text { font: 10px -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; fill: #59636e; }
.l0 { fill: #ebedf0; } .l1 { fill: #c8ccd1; } .l2 { fill: #9ba1a8; } .l3 { fill: #6e7681; } .l4 { fill: #3d444d; }
@media (prefers-color-scheme: dark) {
  text { fill: #9198a1; }
  .l0 { fill: #151b23; } .l1 { fill: #3d444d; } .l2 { fill: #656c76; } .l3 { fill: #9198a1; } .l4 { fill: #d1d7e0; }
}
rect { rx: 2px; }
"""


def fetch(login, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.load(resp)
    if body.get("errors") or not body.get("data", {}).get("user"):
        raise SystemExit(f"GitHub API error: {body.get('errors') or 'user not found'}")
    return body["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def render(cal):
    weeks = cal["weeks"]
    width = LEFT + len(weeks) * STEP + 4
    height = TOP + 7 * STEP + 26
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
           f"<style>{STYLE}</style>"]

    last_month = None
    for x, week in enumerate(weeks):
        first = date.fromisoformat(week["contributionDays"][0]["date"])
        # label each month at the first week starting in it; the last columns are too narrow for a label
        if last_month is not None and first.month != last_month and x < len(weeks) - 2:
            out.append(f'<text x="{LEFT + x * STEP}" y="{TOP - 7}">{first.strftime("%b")}</text>')
        last_month = first.month
        for day in week["contributionDays"]:
            level = LEVELS.index(day["contributionLevel"])
            y = TOP + day["weekday"] * STEP
            out.append(f'<rect class="l{level}" x="{LEFT + x * STEP}" y="{y}" width="{CELL}" height="{CELL}">'
                       f'<title>{day["date"]}</title></rect>')

    for weekday, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        out.append(f'<text x="0" y="{TOP + weekday * STEP + 9}">{name}</text>')

    legend_y = TOP + 7 * STEP + 10
    out.append(f'<text x="{LEFT}" y="{legend_y + 9}">{cal["totalContributions"]} contributions in the last year</text>')
    lx = width - 4 - 5 * STEP - 30
    out.append(f'<text x="{lx - 28}" y="{legend_y + 9}">Less</text>')
    for i in range(5):
        out.append(f'<rect class="l{i}" x="{lx + i * STEP}" y="{legend_y}" width="{CELL}" height="{CELL}"/>')
    out.append(f'<text x="{lx + 5 * STEP + 2}" y="{legend_y + 9}">More</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    login, path = sys.argv[1], sys.argv[2]
    svg = render(fetch(login, os.environ["GITHUB_TOKEN"]))
    assert svg.count("<rect") >= 365, "calendar looks incomplete"
    with open(path, "w") as f:
        f.write(svg)
