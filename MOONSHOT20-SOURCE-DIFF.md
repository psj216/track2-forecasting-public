# Source boundary
Parent:122ad52b3ba28bca06f480b723a0e82502bc77d4.
Executable candidate source:fea15f037f8e085a084aa356cbd1eea2e78dc7c8.
New files: backtesting/moonshot20/adapter.py, Dockerfile, check.py, run.py; .github/workflows/moonshot20.yml.
The original qfbench2_track_forecasting package and FF03 adapter source are unchanged. The candidate Docker context copies only adapter.py, not research scripts, cards, labels, reports or targets. The separate image overrides its own /usr/local/bin/forecast launcher; no old image or tag is overwritten or retagged.
Local AST checks passed. A 4000-cell synthetic joint-grid check passed:700 selected draw IDs,300 unchanged, seed repeat identity, missing-grid rejection. This is execution testing only, not a performance or actual Final schema claim.
Git CLI push lacked credentials; authorized GitHub Git-tree/commit/ref API used on the requested research branch only. PRE remote SHA:039c888943c153f791de7a641384f5a571221aed. The discarded local PRE commit646c267 was never the remote PRE.
