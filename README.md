# Lattice

Lattice helps authors track the source passages behind lessons and guides. Import a source, anchor a card to a unique passage, and compare the evidence when you import a revision. Lattice stores source versions, cards, and review history in a local SQLite file. It needs Python 3.10 or newer and uses only the standard library.

## Local review screen

Run `python app.py` from this directory, then open `http://127.0.0.1:8765` in a browser on the same computer. Stop the server with Ctrl+C. The server binds to loopback on a trusted computer. Local use is single-user. The default database is `lattice.sqlite3` in the directory where you run the command. Use `python app.py --db review.sqlite3` to open a separate project.

1. Enter a source name and paste text or choose a UTF-8 text file. Select **Save source version**.
2. Select that source and add a card. Copy a passage that occurs exactly once, using **View latest source** to inspect the text.
3. Save a revised source under the same name. Compare **Original passage** and **Latest candidate** in the review queue. You can try this with `examples/course-v1.txt` and `examples/course-v2.txt` using `red` as the anchor.
4. Open **Review or edit card** to save edits and record a note for the displayed version. Lattice keeps prior card text and saved notes. Unsaved drafts stay in the current tab while you filter or save the other form. Save review notes before importing a new source version.
5. Choose **Export evidence** to download a JSON copy of the source texts, cards, versions and history. Store it with the same care as the source material.

The browser screen accepts plain text and limits each request to 2 MB. Use the CLI for basic HTML extraction.

## Try the CLI

Run these commands from this directory with a fresh database and an unused export path. If your Python command is `python3`, use it in place of `python`.

```sh
python lattice.py --db demo.sqlite3 import course examples/course-v1.txt
python lattice.py --db demo.sqlite3 card course "First lesson" "The example says red." red
python lattice.py --db demo.sqlite3 import course examples/course-v2.txt
python lattice.py --db demo.sqlite3 queue
python lattice.py --db demo.sqlite3 review 1 "Checked against the revised source; lesson needs editing."
python lattice.py --db demo.sqlite3 export evidence.json
python -m unittest -v
```

Use `python lattice.py --help` and subcommand `--help` for options. A source name identifies successive versions. Anchor text must occur exactly once in the latest version at creation, counting overlaps. Each card has one anchor. Create separate cards for multiple dependencies. Review notes acknowledge a specific source version and preserve the original anchor and card text. CLI export requires an unused path and protects existing files, including the database. The JSON includes complete source texts, cards, edges, versions and review history.

## Interpretation and limitations

`unchanged` means the exact quote occurs once in the latest source or the entire source is unchanged. Check surrounding context manually. `changed` is a tentative candidate between unique nearby text fragments. Unrelated text can form the same boundaries, so inspect the candidate. `unresolvable` means Lattice could not relocate the passage conservatively. Review a deleted, repeated, or relocated passage against the full source before updating a lesson.

Keep separate database files and backups for separate projects. The workflow excludes concurrent edits, migration between schema versions, re-anchoring and JSON import. Basic HTML extraction may omit visual meaning. Extract text separately from PDFs and scans. Source refresh is manual.

## Related tools

For web change monitoring, see [changedetection.io](https://github.com/dgtlmoon/changedetection.io) and [Visualping](https://help.visualping.io/en/articles/14476033). For requirements and documentation traceability, see [StrictDoc](https://github.com/strictdoc-project/strictdoc).

## License

MIT. Original implementation uses the Python standard library.


