# The source article

The paper itself is **not redistributed here** — it is copyrighted by Taylor &
Francis and sits behind a paywall:

> Troster, V. (2018). "Testing for Granger-causality in quantiles."
> *Econometric Reviews* 37(8), 850–866.
> DOI [10.1080/07474938.2016.1172400](https://doi.org/10.1080/07474938.2016.1172400)

## Do I need it to run the reproduction?

Mostly no. Everything the pipeline needs *from* the paper has already been
transcribed into version-controlled files:

- `config/paper_targets.yaml` — Tables 1–4, verbatim, with page references
- `src/qgc/provenance.py` — every modelling choice and where it came from
- `src/qgc/_external_resolutions.py` — the eight gaps D1–D8 and their resolutions

So `data`, `empirical`, `mc`, `supwald` and `compare` all run without it.

The **`figures` stage** is the exception: it rasterises Figures 1–4 out of the PDF
to digitise their curves, since the paper reports its Monte Carlo results only as
images. Without the PDF that stage still runs and still produces our own figures —
it just logs a warning and omits the paper's overlaid curves.

## To enable it

Obtain the article through your institution and save it here as:

```
paper/Testing for Granger-causality in quantiles.pdf
```

Then:

```bash
python run_reproduction.py --full --stages figures,compare --force figures,compare
```

`tools/pdf_extract.py` will also regenerate `paper/extracted_text.txt` if you want
the plain text:

```bash
python tools/pdf_extract.py "paper/Testing for Granger-causality in quantiles.pdf" > paper/extracted_text.txt
```
