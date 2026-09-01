# IntelForge

IntelForge is a CLI-first, evidence-bound research pipeline for creating
validated tactical Points of Information (POIs) for Model United Nations.
It deliberately separates context, mandate, research, evidence, law,
generation, novelty, validation, and persistence so a future GUI can call the
same services.

```bash
python -m intelforge research --committee DISEC --agenda "Preventing weaponisation of critical technologies" --portfolio SGP --freeze-date 2026-01-01 --target-countries China --poi-count 3
```

External integrations are opt-in. Set `INTELFORGE_SEARXNG_URL`,
`INTELFORGE_OLLAMA_URL`, and `GEMINI_API_KEY` when those providers are
available. Without an evidence-bearing discovery source, IntelForge completes
the job safely with zero final POIs rather than fabricating claims.
