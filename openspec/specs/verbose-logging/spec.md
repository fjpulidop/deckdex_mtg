# Verbose Logging

Two levels: normal (progress bars + errors) and verbose (per-card/batch detail). Central config: `deckdex/logger_config.py`; configure_logging(verbose=False|True) → INFO vs DEBUG.

**Normal:** "Connected to spreadsheet…", tqdm progress (cards/s), error count + sample, "Card processing completed successfully". **Verbose:** batch start, per-card fetch with timing, batch write, final stats (total, success, errors, time). Running "cards not found" counter; final list (e.g. up to 10 names). tqdm: description, %, current/total, rate, ETA. Colors: errors red, warnings yellow, success green. Loguru: remove default handler; add INFO or DEBUG. Flush stdout for counter; dry-run: banner "DRY RUN MODE", "DRY RUN:" prefix on simulated ops, summary.
