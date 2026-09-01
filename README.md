# signetry.github.io

> **[Apache-2.0](LICENSE)** — this site is open source. The engine it describes
> ([`signetry-core`](https://github.com/Signetry/core)) is source-available under
> BUSL-1.1 and converts to Apache-2.0 on **2030-08-31**. See
> [LICENSING.md](https://github.com/Signetry/signetry/blob/main/LICENSING.md).

The Signetry landing page — **[signetry.github.io](https://signetry.github.io)**.

## What this is

One hand-written `index.html`. No build step, no framework, no bundler, no
dependencies — the whole page is a single file plus the images in `assets/`.
GitHub Pages serves `main` directly; `.nojekyll` tells it not to run Jekyll over it.

## Previewing a change

```sh
python3 -m http.server 8000    # then open http://localhost:8000
```

Opening `index.html` with `file://` mostly works too, but a local server matches
what Pages actually serves.

## What belongs here

Presentation only. Governance behaviour, detection rules and CLI semantics live in
[`Signetry/core`](https://github.com/Signetry/core) — a change to any of those gets
sent upstream instead.

Good contributions:

- **Accuracy.** A version number, claim, or link on this page that no longer matches
  the code is a bug worth reporting even if you don't fix it.
- **Accessibility.** Contrast, focus states, reduced-motion, screen-reader order.
- **The page without JavaScript, and on a narrow screen.** Both are meant to work.

Keep the single-file, zero-dependency shape. A PR that introduces a build step needs
to argue for it first, in an issue.

## Contributing

Fork, edit `index.html`, open a PR — and say in the description what you looked at
it in, because this page has no test suite and no CI. There is no CLA check wired up
here yet; the [CLA](https://github.com/Signetry/core/blob/main/CLA.md) still governs
accepted contributions, same as every other Signetry repo.

## License

**[Apache-2.0](LICENSE)**, © 2026 Binay Dalai. Copy the layout, fork the page, take
the CSS. The Signetry name and mark are not part of that grant — don't ship a fork
that presents itself as Signetry.
