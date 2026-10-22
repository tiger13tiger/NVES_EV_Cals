# Contributing to nves-au

Thanks for considering a contribution. This is a small, focused toolkit --
please keep changes narrow and in scope for the project brief (an
individual analyst's NVES compliance/credit calculator), rather than
growing it toward DMS/ERP integration, cloud deployment, or an AI
assistant, which are explicitly out of scope for now.

## Setting up

```bash
git clone https://github.com/tiger13tiger/NVES_EV_Cals.git
cd NVES_EV_Cals
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,app]"
```

Run the checks CI runs:

```bash
ruff check nves_au tests
pytest --cov=nves_au --cov-report=term-missing
nves-au demo   # smoke test the console entry point
```

## Hard constraints (please read before a PR)

- **Public data and public regulation only.** No proprietary DMS schemas
  (e.g. Pentana), no former-employer data, code or logic, anywhere in the
  repo -- tests, examples, the synthetic generator, all of it.
- **Every regulatory parameter needs a source.** Nothing in
  `nves_au/engine/` may hard-code a target, slope, reference mass, penalty
  rate or expiry period. If you're adding or changing a number, it goes in
  `config/regulation/*.yaml` with:
  - the source URL(s) you checked it against,
  - the retrieval date,
  - a `confidence` of `confirmed` (read directly from the Act/Rules/a
    Ministerial Determination/official Regulator page) or `unverified`
    (anything else, including professional commentary corroborating each
    other but not primary law).
  - If you can't confirm a value, leave it `unverified` and say so in your
    PR description and, if it affects a headline claim, in the README's
    parameter-verification table.
- **Runs fully local.** No feature should require a network call to
  function (the Green Vehicle Guide / NVES Regulator loaders are explicitly
  manual-download based for this reason) or send user data to a third
  party.
- **No stub/TODO code.** PRs should contain complete, runnable, tested
  code -- not placeholders.

## Testing expectations

- Every formula change needs a test. If you're adding or changing a
  calculation, add at least one hand-calculated worked example (show your
  arithmetic in a comment, like the existing tests do) -- don't just assert
  against the code's own output.
- Run `ruff check` and `pytest` before opening a PR; CI runs both across
  Python 3.11-3.13.
- If you touch the Streamlit app, there's an `AppTest`-based smoke test in
  `tests/test_streamlit_app.py` -- extend it rather than relying on manual
  clicking only.

## Docs

If you change a formula or a config value's meaning, update
`docs/methodology.md` to match (it's meant to be the complete, cited
explanation of every calculation) and both READMEs if it affects the
quick-start or the verification table.

## License

By contributing, you agree your contribution is licensed under this
project's Apache License 2.0 (see [LICENSE](LICENSE)).
