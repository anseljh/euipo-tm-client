# Releasing

Releases are published to [PyPI](https://pypi.org/project/euipo-tm-client/)
automatically by the `.github/workflows/publish.yml` GitHub Actions workflow,
which runs when a **GitHub Release is published**. Publishing uses PyPI
[Trusted Publishing](https://docs.pypi.org/trusted-publishers/) (OIDC) — no API
token is stored in the repo.

## Cutting a release

1. **Bump the version** in `pyproject.toml` (`project.version`). Follow
   [semantic versioning](https://semver.org/).
2. Commit and push to `main`:
   ```bash
   git commit -am "Release vX.Y.Z"
   git push origin main
   ```
3. **Tag and push** the tag:
   ```bash
   git tag -a vX.Y.Z -m "euipo-tm-client X.Y.Z"
   git push origin vX.Y.Z
   ```
4. **Create the GitHub Release** (this triggers the publish workflow):
   ```bash
   gh release create vX.Y.Z --title vX.Y.Z --notes "..."
   ```
5. Watch the run: `gh run watch` (or the repo's Actions tab). On success the new
   version appears on PyPI.

The workflow builds the sdist + wheel, runs `twine check`, then publishes via
the `pypi` GitHub environment.

## Verifying

```bash
# In a throwaway environment, install the just-published version from PyPI:
uv run --no-project --with euipo-tm-client==X.Y.Z python -c "import euipo_tm_client; print('ok')"
```

## Manual / local publish (fallback)

If you ever need to publish without the workflow:

```bash
rm -rf dist && uv build
uvx --from twine twine check dist/*
uvx --from twine twine upload --repository pypi dist/*   # needs a PyPI token in ~/.pypirc
```

Use `--repository testpypi` to dry-run against
[TestPyPI](https://test.pypi.org/project/euipo-tm-client/) first. Note that
**a version number can never be reused** once uploaded to (Test)PyPI — bump the
version to re-publish.

## One-time setup (already done)

- **PyPI Trusted Publisher** configured at
  `https://pypi.org/manage/project/euipo-tm-client/settings/publishing/` →
  Owner `anseljh`, Repo `euipo-tm-client`, Workflow `publish.yml`, Environment
  `pypi`.
- **GitHub `pypi` environment** created (optionally add required reviewers to
  gate publishing behind manual approval).
