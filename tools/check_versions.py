#!/usr/bin/env python3
"""Fail when a version printed on the landing page no longer matches the repository.

``index.html`` is hand-written with no build step, so every version string on it is a
claim maintained by hand — and the install command is one of them. A visitor who copies
a stale pin installs a release behind, which is a worse first impression than showing no
version at all. This check is what stops that drifting silently.

The rules, one per kind of value the page prints:

  ``vX.Y.Z``   must equal the repository's newest semver tag.
  ``@vN``      a deliberately moving major pin — the tag must exist, but may point
               anywhere. Not compared against the newest release.
  ``—``        asserts *no release exists*. Fails if the repository has any tag, because
               an em dash means "not measured" everywhere else in this project and must
               not quietly stand in for "we forgot".
  ``docs``     not a version. Skipped.

Run locally with ``python3 tools/check_versions.py``. Unauthenticated requests are
enough for six public repositories; CI passes ``GITHUB_TOKEN`` to avoid the rate limit.
Exits 0 when every claim matches, 1 with every mismatch listed — all of them, not just
the first, so one run tells you everything to change.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.github.com"
PAGE = Path(__file__).resolve().parent.parent / "index.html"

# One row of the registry table. Matched as a whole anchor rather than as
# "an href ... then somewhere later an rt span": a `.*?` across arbitrary distance
# will happily pair a link outside the table with the first cell inside it, silently
# skipping the row that link is not. That bug hid a real mismatch during development,
# and a checker that passes while checking nothing is worse than no checker.
ROW_RE = re.compile(
    r'<a class="reg-row"[^>]*href="https://github\.com/Signetry/(?P<repo>[\w.-]+)"'
    r'(?P<body>(?:(?!</a>).)*?)</a>',
    re.DOTALL,
)
RT_RE = re.compile(r'<span class="rt">(?P<version>[^<]*)</span>')

# Standalone `core@vX.Y.Z` pins outside the table — the hero ref line and, more
# importantly, the install command a visitor copies.
PIN_RE = re.compile(r"core@(?P<version>v\d+\.\d+\.\d+)")

SEMVER_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
MOVING_RE = re.compile(r"^@?v(\d+)$")
NOT_A_VERSION = {"docs"}
NO_RELEASE = {"—", "-", "–"}


def _tags(repo: str) -> list[str]:
    """Every tag name in a repository, newest page first."""
    request = urllib.request.Request(
        f"{API}/repos/Signetry/{repo}/tags?per_page=100",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "signetry-site-check"},
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=30) as response:
        return [t["name"] for t in json.load(response)]


def _newest_semver(tags: list[str]) -> str | None:
    """The highest semver tag, compared numerically.

    Sorting these as strings would rank v0.9.0 above v0.10.0 and report a false
    mismatch — the failure mode a version checker least wants to have.
    """
    parsed = [(tuple(int(g) for g in m.groups()), t)
              for t in tags if (m := SEMVER_RE.match(t))]
    return max(parsed)[1] if parsed else None


def main() -> int:
    html = PAGE.read_text(encoding="utf-8")
    problems: list[str] = []
    checked = 0

    matches = list(ROW_RE.finditer(html))
    # A row present in the markup but not matched here would be a claim nobody checked,
    # so the count is asserted rather than assumed. Same reason the parse failing
    # outright is an error and not a skip.
    declared = html.count('class="reg-row"')
    if not matches:
        print("error: found no registry rows in index.html — has the markup changed?",
              file=sys.stderr)
        return 1
    if len(matches) != declared:
        print(f"error: index.html has {declared} registry row(s) but this check parsed "
              f"{len(matches)}. Fix the parser before trusting the result.",
              file=sys.stderr)
        return 1

    rows = []
    for match in matches:
        cell = RT_RE.search(match.group("body"))
        if cell is None:
            problems.append(f"{match.group('repo')}: row prints no version cell")
            continue
        rows.append((match.group("repo"), cell.group("version")))

    for repo, printed in rows:
        printed = printed.strip()
        if printed in NOT_A_VERSION:
            continue

        try:
            tags = _tags(repo)
        except urllib.error.HTTPError as exc:
            problems.append(f"{repo}: cannot read tags ({exc.code} {exc.reason})")
            continue
        except urllib.error.URLError as exc:
            problems.append(f"{repo}: cannot reach the API ({exc.reason})")
            continue

        checked += 1

        if printed in NO_RELEASE:
            if tags:
                problems.append(
                    f"{repo}: page shows '{printed}' (no release) but the newest tag is "
                    f"{_newest_semver(tags) or tags[0]}"
                )
        elif MOVING_RE.match(printed):
            tag = printed.lstrip("@")
            if tag not in tags:
                problems.append(f"{repo}: page pins {printed} but no tag {tag} exists")
        elif SEMVER_RE.match(printed):
            newest = _newest_semver(tags)
            if newest and printed != newest:
                problems.append(f"{repo}: page shows {printed}, newest release is {newest}")
        else:
            problems.append(f"{repo}: unrecognised version string {printed!r}")

    # The install command and hero ref line, which the table does not cover.
    pins = set(PIN_RE.findall(html))
    if pins:
        try:
            newest_core = _newest_semver(_tags("core"))
        except (urllib.error.HTTPError, urllib.error.URLError) as exc:
            problems.append(f"core: cannot verify inline pins ({exc})")
        else:
            checked += 1
            for pin in sorted(pins):
                if newest_core and pin != newest_core:
                    problems.append(
                        f"core@{pin} appears inline (install command / ref line) but the "
                        f"newest release is {newest_core}"
                    )

    if problems:
        print(f"{len(problems)} version claim(s) on index.html no longer hold:\n",
              file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        print("\nUpdate index.html to match, or correct the repository's tags.",
              file=sys.stderr)
        return 1

    print(f"index.html: every version claim matches ({checked} source(s) checked).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
