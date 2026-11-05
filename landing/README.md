# OdorMap landing page

A static, single-page site with no build step. Deploy the contents of this
folder as-is to any static host (GitHub Pages, Netlify, Cloudflare Pages, ...).

```
index.html                 page markup
styles.css                 styles (palette follows .streamlit/config.toml)
main.js                    keyboard-accessible tabs for the examples
assets/structures/*.svg    RDKit 2D structure drawings
assets/fonts/              self-hosted Newsreader, Public Sans, IBM Plex Mono (+ OFL licences)
assets/favicon.svg
```

Preview locally:

```bash
python3 -m http.server --directory landing 8000
```

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
