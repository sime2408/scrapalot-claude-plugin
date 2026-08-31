# Scrapalot Claude Code plugin

The published home of the **Scrapalot AI Toolkit** — the Claude Code commands,
skills, agents and hooks that run the [Scrapalot](https://scrapalot.app) stack.

```bash
claude plugin marketplace add https://api.scrapalot.app/marketplace.json
claude plugin install scrapalot@scrapalot
```

Everything lands under one namespace: `/scrapalot:book`, `/scrapalot:rag-test`,
`/scrapalot:devops-loop`, and agents as `scrapalot:rag-tester`. Update later with
`claude plugin update scrapalot`.

**[plugin/README.md](plugin/README.md) is the real documentation** — what each
part does, what it expects from your environment, where run state is written and
what the hooks guard.

## Layout

| Path | What it is |
|---|---|
| `plugin/` | The bundle itself. This is what gets installed. |
| `.claude-plugin/marketplace.json` | The marketplace manifest, served at `https://api.scrapalot.app/marketplace.json`. Generated — do not hand-edit. |
| `build-marketplace.py` | Regenerates the manifest from the bundle. `--check` fails when the committed copy has drifted. |

The manifest carries a full inventory — every command, skill, agent and hook with
its description — so the roster is readable without cloning.

## How this repo is maintained

The bundle is authored in the private Scrapalot workspace and mirrored here in
one direction. Pull requests that change `plugin/` will be overwritten by the
next mirror push; open an issue instead. `api.scrapalot.app/marketplace.json`
proxies `main` of this repo directly, so a merge here is the release.

## License

MIT — see [LICENSE](LICENSE).
