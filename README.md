# ls0775.github.io

Personal static site and blog publishing target.

## Blog publishing pipeline

Blog source content is maintained in `ls0775/homelab` at `docs/blogs/` and synced into this repository as static pages.

- Source calendar is parsed from: `docs/blogs/README.md`
- Supplemental posts can be pinned locally in `scripts/sync_blogs.py` when a published page should exist even if it is not yet listed in the source calendar
- Published pages are generated under: `blog/`
- Future-dated posts are hidden until their publish date

### Manual sync

```bash
python3 scripts/sync_blogs.py
```

The script uses `GH_TOKEN` when set, otherwise falls back to `gh auth token`.

### Automated sync

GitHub Actions workflow `.github/workflows/sync-blogs.yml` runs:
- on demand via `workflow_dispatch`
- daily on schedule

If generated blog output changes, it commits and pushes updates automatically.

### Required secret for private source repo

Set repository secret `HOMELAB_REPO_TOKEN` (PAT with `repo` read access to `ls0775/homelab`).

Example:

```bash
gh secret set HOMELAB_REPO_TOKEN --repo ls0775/ls0775.github.io
```
