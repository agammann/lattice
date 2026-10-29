# Lattice

A local-first **alpha research prototype** for tracking which authored cards depend on source passages. Import a text or HTML source, anchor a card to a unique passage, import a new version, and inspect evidence for review. No account, network, model, or third-party package is required. This is not proof of market fit or a safety assessment.

## Local review screen

Run `python app.py` and visit `http://127.0.0.1:8765`. Stop it with Ctrl+C. The server listens only on loopback; use it on a trusted computer and do not expose it to a network. It uses a session token and checks the loopback host, but is not designed for multi-user hosting. Paste text or select a UTF-8 text file, add a card using an exact unique passage, then import a new version under the same source name. Review the queue, edit the card, acknowledge the displayed version, or export evidence. The UI preserves prior card text and review notes. The UI does not import HTML or PDF; the CLI supports basic HTML extraction. The server limits requests to 2 MB.

## Try the CLI

Requires Python 3.10 or newer. Run from this directory:

```sh
python lattice.py --db demo.sqlite3 import course examples/course-v1.txt
python lattice.py --db demo.sqlite3 card course "First lesson" "The example says red." red
python lattice.py --db demo.sqlite3 import course examples/course-v2.txt
python lattice.py --db demo.sqlite3 queue
python lattice.py --db demo.sqlite3 review 1 "Checked against the revised source; lesson needs editing."
python lattice.py --db demo.sqlite3 export evidence.json
python -m unittest -v
```

Use `python lattice.py --help` and subcommand `--help` for options. A source name identifies successive versions. Anchor text must occur exactly once in the latest version at creation. Each card currently has one edge; create multiple cards for multiple dependencies. Review notes acknowledge a specific latest version and do not move the original anchor or change the card. CLI export requires a new destination and refuses to overwrite an existing file, including the database. The JSON export contains the complete source texts, cards, edges, versions and review history: treat it as sensitive if your inputs are sensitive.

## Interpretation and limitations

`unchanged` means the exact quote occurs once in the latest source, or the entire source is unchanged. It does not prove the surrounding context or claim remains valid. `changed` is a tentative candidate bounded by unique nearby text; inspect it manually. `unresolvable` means relocation cannot be made conservatively. The heuristic can misidentify a candidate when unrelated text happens to form matching boundaries; a deleted quote or changed context may require manual review. No status establishes truth. Source versions, cards and notes remain in SQLite; use separate database files for separate projects. Concurrent edits, migration between schema versions, re-anchoring, JSON import are not yet supported. Use backups. HTML extraction is basic and may reorder or omit visual meaning. PDFs and OCR are not supported; manually extract text first. No crawler, search or automated source refresh is included. The browser UI is an early prototype and its rendered workflow has not been verified in the restricted development environment.

## Why explore this?

[changedetection.io](https://github.com/dgtlmoon/changedetection.io) monitors changes; [Visualping](https://help.visualping.io/en/articles/14476033) provides hosted monitoring and alerts. Lattice explores an explicit passage-to-lesson review queue rather than monitoring. [StrictDoc](https://github.com/strictdoc-project/strictdoc) already offers requirements and documentation traceability and is a close alternative. Whether this smaller educator workflow is actually better remains unvalidated; this is not a uniqueness claim.

## License

MIT. Original implementation uses the Python standard library.


