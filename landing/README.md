# OdorMap landing page

A static, single-page site with no build step. Deploy the contents of this
folder as-is to any static host (GitHub Pages, Netlify, Cloudflare Pages, ...).

```
index.html                 page markup
styles.css                 styles (dark theme: ink ground, one teal accent, amber for warnings)
main.js                    keyboard-accessible tabs for the examples, nav/header state
motion.js                  animation layer (skipped under prefers-reduced-motion)
assets/structures/*.svg    RDKit 2D structure drawings (light-on-dark)
assets/fonts/              self-hosted Newsreader, Public Sans, IBM Plex Mono (+ OFL licences)
assets/favicon.svg
```

Preview locally:

```bash
python3 -m http.server --directory landing 8000
```

## Motion

`motion.js` only changes how existing content is presented; it never invents
data and never generates intermediate numbers (every value is its real text from
the first frame).

- **Hero loop.** The hero's vanillin drawing is the RDKit SVG file, inlined and
  run as a continuous loop: bonds draw in from the first SMILES atom outward,
  hold, retract in the same order, and start again. The dashed ring, the glow
  and the drifting skeletal fragments behind the hero are generic decoration,
  not data, and stand for no molecule.
- **Method stage.** A pinned copy of the same drawing changes state as the four
  method steps scroll past: atoms light in SMILES order (Parse), bonds within
  one and two bonds of each atom in the real bond graph (Fingerprint),
  vanillin's recorded top-5 scores (Score), and the vanillin example's
  training-set warning (Rank and flag). It is `aria-hidden`; the step text
  carries the content.
- **Examples / Evaluation.** Tab switches redraw the structure once and grow the
  score bars; the reliability curve plots itself once when scrolled into view.

All continuous loops pause when offscreen (IntersectionObserver) or when the tab
is hidden (visibilitychange). A "Pause motion" / "Play motion" toggle in the
corner of the hero drawing (a `<button aria-pressed>`) freezes all of them on
demand (WCAG 2.2.2); the choice is kept in `localStorage` (`om-motion-paused`)
and applied by the head script before first paint. The toggle only exists when
motion runs, so it is not shown under reduced motion. With `prefers-reduced-motion: reduce`, or without
JavaScript, nothing animates and every section is visible as written (without
JavaScript all nine examples are stacked). If `motion.js` fails to start, the
head script removes the `motion` class after 3 s so nothing stays hidden.

## Where the content comes from

- Example predictions: copied from `results/predict_examples.md`.
- Metrics: `results/baseline.md` (macro ROC-AUC) and `results/calibration.md`
  (ECE, reliability bins).
- Structure drawings: regenerate with `python scripts/make_landing_assets.py`.

If those result files are regenerated, update the numbers in `index.html` by hand.

## Before deploying

- The demo button is a placeholder (`Live demo link added at deploy`). Replace
  the `<span class="btn btn-placeholder">` in the hero with a link once the app
  has a public URL.
- Links to `results/*.md` point at the `main` branch of
  https://github.com/Sid13SST/OdorMap and resolve once these files are on `main`.
- Dataset terms: the Leffingwell Odor Dataset is CC-BY-NC 4.0
  (Zenodo DOI 10.5281/zenodo.4085097). Keep the attribution and the
  non-commercial note on any deployed copy.
