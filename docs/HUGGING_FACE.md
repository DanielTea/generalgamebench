# Hugging Face publication design

The same static leaderboard can be hosted on danieltremer.com, Sites or a Hugging Face Space. Relative media and data URLs work under each host. The Space is a display layer; game installation, provider sign-ins and evaluation execution remain on separate workers.

Prepare a portable Space and a separate Dataset without uploading anything:

```sh
uv run python scripts/export_huggingface.py --output build/huggingface-preview
```

The Space folder includes the HTML, data, media credits and `sdk: static` metadata. The Dataset folder contains JSONL configurations for each nonempty track, with one row per agent/game. It retains exact model identifiers, local weight revisions, seeds, decision horizons, latency eligibility, hardware and trust status. The suite identifier includes task/engine metadata, and every row records the exact source snapshot checksum. A checksum manifest covers the export. Neither credentials nor proprietary game installations belong in either repository.

The v0.3 export preserves the frozen v0.2 model and baseline rows (33 scenarios). Its Space also displays the current integration catalog (43 scenarios across 36 cards), clearly separated from those rankings. The ten new tasks have independent integration-control evidence in the v0.3 release. Native diagnostic previews of unadmitted games never become Dataset score rows. A future complete model rerun must publish a new suite identity and version instead of mixing additional games into historical scores.

Future publication should upload these folders into separate Space and Dataset repositories, using a narrowly scoped token supplied outside the code. Keep the scored snapshot immutable and link the Dataset revision from the Space. Model cards can link to the same evidence revision. A submission service and isolated evaluation workers are separate infrastructure; a static Space must never execute uploaded agent code.

Raw replay evidence remains in versioned releases. Game-frame licensing must be reviewed separately before adding frames to a Dataset. A model being downloadable on the Hub is not permission to redistribute its weights.

References: [Static Spaces](https://huggingface.co/docs/hub/spaces-sdks-static), [Dataset configurations](https://huggingface.co/docs/hub/datasets-data-files-configuration).
