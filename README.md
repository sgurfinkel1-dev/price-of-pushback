# The Price of Pushback

Measures how far a model moves its stated probability under content-free pushback,
in the same units as real evidence (the Pushback Bayes Factor; norm = 1).
Built for the Apart Research AI x Epistemics Sprint, November 2026.
All code was written during the sprint; nothing is pre-existing.

- `run.py <model> [n_items] [workers]` generates the scenarios and runs them through the Claude Code CLI (`python run.py` alone runs a self-check)
- `analyze.py` computes statistics (`stats.json`) and figures
- `build_report.py` builds the report
- `results/` full transcripts, `report/` the report (Word and PDF)
