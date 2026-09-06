# French Drill

Two modes, toggled at the top of the page:

- **Temps** — drills *which tense the context demands* (not mechanical
  conjugation). Main event: imparfait vs conditionnel; also passé
  composé/imparfait, conditionnel/futur simple, and subjonctif triggers.
- **Genre** — drills masculin vs féminin on ~700 common nouns. Answer with
  the buttons or the **M** / **F** keys; feedback shows the article
  (le musée, l'image…) plus the ending-pattern rule or trap when one applies
  (-age → m except plage/page/image/cage; -ée → f except musée/lycée/trophée…).

## Run

**Double-click `Start French Drill.command`.** A Terminal window opens (that's
the app's server — leave it open while you drill) and the app opens in your
browser at **http://localhost:8642** automatically.

Equivalent from a terminal: `python3 server.py` in this folder.

Don't open `index.html` directly (double-clicking it in Finder) — the page
needs its server to load the item banks and save progress, so it will just
show an error telling you to launch the server.

The port is deliberately distinct from the other local apps (pdf-search sits
on 8123, library-browser on 4242); if 8642 is ever busy the server hops to
the next free port and prints a note, or set `PORT=...` yourself.

## Use

- Type the conjugated form, Enter to check, Enter again for the next item.
- Missing accents with the right tense still count as correct — the accented
  form is shown.
- Every attempt is logged to `progress.json`. In tense mode, selection is
  weighted toward the tense pairs you miss most (smoothed error rate over the
  last 200 attempts). In gender mode it adapts per word: words you last got
  wrong are heavily favored (~50 %), then unseen words, then review of known
  ones.
- **Fin de session** shows per-pair accuracy for this session (including a
  masculin-vs-féminin row) plus your weakest pair overall.

## AI-generated items (optional)

```
ANTHROPIC_API_KEY=sk-... python3 server.py
```

The **+ 5 items IA** button then generates fresh items for the selected pair
(model via `ANTHROPIC_MODEL`, default `claude-sonnet-5`). Generated items are
served next but are session-only — they aren't written into `items.json`.
Without a key the button degrades gracefully to the static bank.

## Files

- `items.json` — tense seed bank (62 items: 30 imparfait/conditionnel,
  12 PC/imparfait, 8 conditionnel/futur, 12 subjonctif). Each item: sentence
  with `___`, infinitive, answer (+ accepted alternates), tense, and a
  one-line *why*.
- `nouns.json` — gender bank (694 nouns: `w` word, `g` m/f, `e` gloss,
  optional `n` note for pattern/trap words, optional `a` article override for
  h-words like « la honte » vs « l'hôtel »). Includes both readings of the
  homographs le/la tour, mode, poste, manche, voile.
- `progress.json` — attempt log (created on first answer). Delete to reset.
