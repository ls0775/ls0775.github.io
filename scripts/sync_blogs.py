#!/usr/bin/env python3
"""Sync and publish blog posts from ls0775/homelab docs/blogs."""

from __future__ import annotations

import base64
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SOURCE_OWNER = "ls0775"
SOURCE_REPO = "homelab"
SOURCE_BRANCH = "main"
SOURCE_BLOG_ROOT = "docs/blogs"
API_BASE = "https://api.github.com"
BLOG_ROOT = Path(__file__).resolve().parent.parent / "blog"
SUPPLEMENTAL_POSTS = (
    {
        "number": 0,
        "title": "Post 00 — What Is a Homelab? A Plain-English Guide to This Project",
        "filename": "post-00-what-is-a-homelab.md",
        "publish_date": "2026-04-08",
    },
)

CALENDAR_ROW_RE = re.compile(
    r"^\|\s*(\d+)\s*\|\s*\[(.+?)\]\(\./(post-\d{2}[^)]+\.md)\)\s*\|\s*[^|]*\|\s*(\d{4}-\d{2}-\d{2})\s*\|$"
)
TITLE_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
POST_LINK_RE = re.compile(r"\(\./(post-\d{2}[^)]+)\.md\)")


@dataclass(frozen=True)
class Post:
    number: int
    title: str
    source_filename: str
    publish_date: dt.date
    markdown: str

    @property
    def slug(self) -> str:
        return Path(self.source_filename).stem

    @property
    def url(self) -> str:
        return f"/blog/{self.slug}/"

    @property
    def date_label(self) -> str:
        return f"{self.publish_date.day} {self.publish_date.strftime('%B %Y')}"


def _read_token() -> str:
    env_token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    if env_token:
        return env_token.strip()

    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.SubprocessError, FileNotFoundError) as exc:
        raise RuntimeError(
            "No GitHub token available. Set GH_TOKEN or authenticate with `gh auth login`."
        ) from exc

    token = result.stdout.strip()
    if not token:
        raise RuntimeError("`gh auth token` returned an empty token.")
    return token


def _api_request(token: str, path: str, *, method: str = "GET", payload: dict[str, Any] | None = None) -> Any:
    body = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        f"{API_BASE}{path}",
        data=body,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req) as response:
            content_type = response.headers.get("Content-Type", "")
            body = response.read()
            if "application/json" in content_type:
                return json.loads(body.decode("utf-8"))
            return body.decode("utf-8")
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API {method} {path} failed: {exc.code} {details}") from exc


def _fetch_repo_file(token: str, repo_path: str) -> str:
    result = _api_request(
        token,
        f"/repos/{SOURCE_OWNER}/{SOURCE_REPO}/contents/{repo_path}?ref={SOURCE_BRANCH}",
    )
    if result.get("encoding") != "base64":
        raise RuntimeError(f"Unexpected encoding for {repo_path}: {result.get('encoding')}")
    raw = base64.b64decode(result["content"])
    return raw.decode("utf-8")


def _render_markdown(token: str, markdown: str) -> str:
    result = _api_request(
        token,
        "/markdown",
        method="POST",
        payload={"text": markdown, "mode": "gfm", "context": f"{SOURCE_OWNER}/{SOURCE_REPO}"},
    )
    if not isinstance(result, str):
        raise RuntimeError("Unexpected markdown render response from GitHub API.")
    return result


def _parse_calendar(readme_markdown: str) -> list[tuple[int, str, str, dt.date]]:
    posts: list[tuple[int, str, str, dt.date]] = []
    for line in readme_markdown.splitlines():
        match = CALENDAR_ROW_RE.match(line.strip())
        if not match:
            continue
        number = int(match.group(1))
        title = match.group(2).strip()
        filename = match.group(3).strip()
        publish_date = dt.date.fromisoformat(match.group(4))
        posts.append((number, title, filename, publish_date))

    if not posts:
        raise RuntimeError("Could not parse any calendar rows from docs/blogs/README.md.")
    return posts


def _merge_supplemental_posts(
    posts: list[tuple[int, str, str, dt.date]],
) -> list[tuple[int, str, str, dt.date]]:
    seen_filenames = {filename for _, _, filename, _ in posts}
    merged = list(posts)

    for extra in SUPPLEMENTAL_POSTS:
        if extra["filename"] in seen_filenames:
            continue
        merged.append(
            (
                int(extra["number"]),
                str(extra["title"]),
                str(extra["filename"]),
                dt.date.fromisoformat(str(extra["publish_date"])),
            )
        )

    return merged


def _extract_fallback_title(markdown: str) -> str:
    match = TITLE_RE.search(markdown)
    if match:
        return match.group(1).strip()
    return "Untitled Post"


def _prepare_markdown(markdown: str) -> str:
    # Drop the first top-level heading to avoid duplicating the page title header.
    lines = markdown.splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    prepared = "\n".join(lines).lstrip()

    # Rewrite in-series links to published blog URLs.
    prepared = POST_LINK_RE.sub(r"(/blog/\1/)", prepared)
    return prepared


def _template(page_title: str, content_html: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <meta name="theme-color" content="#0a0a0c">
    <title>{page_title}</title>
    <link rel="icon" type="image/png" href="/favicon.png">
    <link rel="stylesheet" href="/blog/blog.css">
</head>
<body>
    <main class="page">
{content_html}
    </main>
</body>
</html>
"""


def _render_post_html(post: Post, rendered_markdown_html: str) -> str:
    content = f"""        <header class="post-header">
            <a class="back-link" href="/blog/">&larr; Blog</a>
            <h1>{post.title}</h1>
            <p class="post-date">{post.date_label}</p>
        </header>
        <article class="prose">
{rendered_markdown_html}
        </article>
"""
    return _template(f"{post.title} | ls0775 blog", content)


def _render_index_html(posts: list[Post]) -> str:
    items = "\n".join(
        f"""            <li>
                <a href="{post.url}">{post.title}</a>
                <time datetime="{post.publish_date.isoformat()}">{post.date_label}</time>
            </li>"""
        for post in posts
    )
    content = f"""        <header class="index-header">
            <a class="back-link" href="/">&larr; Home</a>
            <h1>Blog</h1>
            <p>Notes from building and operating my homelab.</p>
        </header>
        <section class="post-list-wrap">
            <ol class="post-list">
{items}
            </ol>
        </section>
"""
    return _template("Blog | ls0775", content)


def _ensure_static_assets() -> None:
    BLOG_ROOT.mkdir(parents=True, exist_ok=True)


def _clear_stale_post_dirs(published_slugs: set[str]) -> None:
    for child in BLOG_ROOT.iterdir():
        if child.is_dir() and child.name.startswith("post-") and child.name not in published_slugs:
            shutil.rmtree(child)


def main() -> None:
    token = _read_token()
    _ensure_static_assets()

    calendar_md = _fetch_repo_file(token, f"{SOURCE_BLOG_ROOT}/README.md")
    calendar_rows = _merge_supplemental_posts(_parse_calendar(calendar_md))

    posts: list[Post] = []
    today = dt.date.today()
    for number, calendar_title, filename, publish_date in calendar_rows:
        markdown = _fetch_repo_file(token, f"{SOURCE_BLOG_ROOT}/{filename}")
        markdown = _prepare_markdown(markdown)
        title = calendar_title or _extract_fallback_title(markdown)
        post = Post(
            number=number,
            title=title,
            source_filename=filename,
            publish_date=publish_date,
            markdown=markdown,
        )
        if post.publish_date <= today:
            posts.append(post)

    posts.sort(key=lambda p: (p.publish_date, p.number), reverse=True)
    published_slugs = {post.slug for post in posts}
    _clear_stale_post_dirs(published_slugs)

    for post in posts:
        rendered = _render_markdown(token, post.markdown)
        post_dir = BLOG_ROOT / post.slug
        post_dir.mkdir(parents=True, exist_ok=True)
        (post_dir / "index.html").write_text(_render_post_html(post, rendered), encoding="utf-8")

    (BLOG_ROOT / "index.html").write_text(_render_index_html(posts), encoding="utf-8")
    print(f"Published {len(posts)} post(s) to {BLOG_ROOT}")


if __name__ == "__main__":
    main()
