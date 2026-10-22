# Regulatory parameter configs

This directory is the **single source of truth** for every numeric NVES
parameter used by the calculation engine. Nothing in `nves_au/engine/` may
hard-code a target, slope, reference mass, penalty rate or expiry period —
every formula reads these values from here.

Each file carries:
- `meta.retrieved` — the date this file's values were last checked against
  an official or professional source (ISO date).
- `meta.sources` — the URLs consulted, with a short note on what each one
  gave us.
- `meta.confidence` — `confirmed` (seen on an NVES Regulator / Department of
  Infrastructure / Federal Register page, or in the Regulator's own
  guidance notes) or `unverified` (secondary/professional commentary only,
  or explicitly flagged by the source itself as subject to change). Anything
  `unverified` MUST also appear in the project README's parameter-verification
  table and must not be presented to a user as final.

## Known limitations of this research pass (2026-10-22)

This pass was done with web search only — direct fetches to
legislation.gov.au, nvesregulator.gov.au and infrastructure.gov.au were
blocked by this session's network egress policy (403 at the proxy for every
external host tried, including non-government sites). Nothing here has been
read from the primary legislative text (the NVES Act 2024, the NVES Rules,
or Ministerial Determinations) directly — it is reconstructed from the
Department of Infrastructure's published guidance note, the NVES Regulator's
own web pages as summarised by search, and corroborating professional/legal
commentary (ICCT, DieselNet, BDO, Bartier, Pitcher, Moulis Legal, Loopit).
Where only one type of source backs a figure, or a source itself says the
value may change, it is marked `unverified`.

**Before this tool is used for any real compliance decision, every
`confirmed` and `unverified` value here must be re-checked by a human
against:**
- New Vehicle Efficiency Standard Act 2024 (Cth) — legislation.gov.au, C2024A00034
- New Vehicle Efficiency Standard Rules / Determinations — legislation.gov.au, F2024L01569 and successors
- NVES Regulator guidance — nvesregulator.gov.au
- Department of Infrastructure NVES numerical precision and calculations guidance note
