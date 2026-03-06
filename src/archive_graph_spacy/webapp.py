"""Small local web app for refreshing and viewing graph visualizations."""

from __future__ import annotations

import argparse
import html
import json
import re
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import duckdb

from archive_graph_spacy.extract import extract_message_mentions
from archive_graph_spacy.io import load_export_bundle
from archive_graph_spacy.link import link_mentions_to_people
from archive_graph_spacy.models import Contact, Message
from archive_graph_spacy.scripts.build_edges import build_edges
from archive_graph_spacy.scripts.visualize_ego import render_ego_graph
from archive_graph_spacy.scripts.visualize_graph import render_graph

LABEL_COLORS = {
    "PERSON": "#fef08a",
    "PERSON_CANDIDATE": "#fde68a",
    "EMAIL": "#bfdbfe",
    "PHONE": "#fecaca",
}

SpanMeta = dict[str, str]


def discover_bundles(base_dir: Path) -> list[Path]:
    bundles: list[Path] = []
    for relative in ("data_exports", "data_samples"):
        root = base_dir / relative
        if not root.exists():
            continue
        if relative == "data_samples" and ((root / "sample_contacts.jsonl").exists() or (root / "contacts.jsonl").exists()):
            bundles.append(root)
            continue
        for child in sorted(root.iterdir()):
            if not child.is_dir():
                continue
            if (child / "contacts.jsonl").exists() or (child / "sample_contacts.jsonl").exists():
                bundles.append(child)
    return bundles


def list_people(derived_dir: Path) -> list[tuple[str, str]]:
    edge_path = derived_dir / "person_person_edges.jsonl"
    if edge_path.exists():
        con = duckdb.connect()
        rows = con.execute(
            """
            WITH people AS (
                SELECT person_a_id AS person_id, person_a_name AS person_name, person_a_type AS person_type
                FROM read_json_auto(?)
                UNION ALL
                SELECT person_b_id AS person_id, person_b_name AS person_name, person_b_type AS person_type
                FROM read_json_auto(?)
            )
            SELECT DISTINCT person_id, person_name
            FROM people
            WHERE person_type = 'person'
            ORDER BY person_name, person_id
            """,
            [str(edge_path), str(edge_path)],
        ).fetchall()
        return [(row[0], row[1]) for row in rows]

    contacts_path = derived_dir.parent / "contacts.jsonl"
    if not contacts_path.exists():
        contacts_path = derived_dir.parent / "sample_contacts.jsonl"
    if not contacts_path.exists():
        return []

    people: list[tuple[str, str]] = []
    for line in contacts_path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("entity_type", "unknown") == "person":
            people.append((row["person_id"], row["display_name"]))
    return sorted(set(people), key=lambda item: (item[1], item[0]))


def load_bundle(bundle: Path) -> tuple[list[Contact], list[Message]]:
    return load_export_bundle(bundle)


def _normalize_email(value: str) -> str:
    return value.strip().casefold()


def explicit_participant_ids(message: Message, contacts: list[Contact]) -> set[str]:
    contact_by_email = {
        _normalize_email(email): contact.person_id
        for contact in contacts
        for email in contact.emails
    }
    ids: set[str] = set()
    sender = _normalize_email(message.sender)
    if sender in contact_by_email:
        ids.add(contact_by_email[sender])
    for recipient in message.recipients:
        normalized = _normalize_email(recipient)
        if normalized in contact_by_email:
            ids.add(contact_by_email[normalized])
    return ids


def highlight_mentions(message: Message, contacts: list[Contact]) -> tuple[str, list[dict[str, object]]]:
    text = f"Subject: {message.subject}\n\n{message.body}".strip()
    mentions = extract_message_mentions(message)
    linked = link_mentions_to_people(
        mentions,
        contacts,
        preferred_person_ids=explicit_participant_ids(message, contacts),
    )

    spans: list[tuple[int, int, SpanMeta]] = []
    seen_mentions: set[tuple[str, str]] = set()
    for mention in mentions:
        key = (mention.text, mention.label)
        if key in seen_mentions:
            continue
        seen_mentions.add(key)
        pattern = re.compile(re.escape(mention.text), re.IGNORECASE)
        for match in pattern.finditer(text):
            spans.append((match.start(), match.end(), {"text": mention.text, "label": mention.label}))

    spans.sort(key=lambda item: (item[0], -(item[1] - item[0])))
    selected: list[tuple[int, int, SpanMeta]] = []
    last_end = -1
    for start, end, meta in spans:
        if start < last_end:
            continue
        selected.append((start, end, meta))
        last_end = end

    parts: list[str] = []
    cursor = 0
    for start, end, meta in selected:
        parts.append(html.escape(text[cursor:start]))
        color = LABEL_COLORS.get(str(meta["label"]), "#e5e7eb")
        tooltip = f"{meta['label']}: {meta['text']}"
        parts.append(
            f'<mark style="background:{color}; padding:2px 4px; border-radius:4px;" '
            f'title="{html.escape(tooltip)}">{html.escape(text[start:end])}</mark>'
        )
        cursor = end
    parts.append(html.escape(text[cursor:]))

    mention_rows: list[dict[str, object]] = []
    for mention in mentions:
        candidates = linked.get(mention.text, [])
        mention_rows.append(
            {
                "text": mention.text,
                "label": mention.label,
                "source": mention.source,
                "candidates": [
                    {
                        "person_id": candidate.person_id,
                        "score": candidate.score,
                        "reasons": ", ".join(candidate.reasons),
                    }
                    for candidate in candidates[:3]
                ],
            }
        )

    return "".join(parts).replace("\n", "<br>\n"), mention_rows


def render_message_page(bundle: Path, message_id: str) -> str:
    contacts, messages = load_bundle(bundle)
    message = next((item for item in messages if item.message_id == message_id), None)
    if message is None:
        raise FileNotFoundError(message_id)
    person_ids = explicit_participant_ids(message, contacts)
    contact_by_id = {contact.person_id: contact for contact in contacts}
    highlight_html, mention_rows = highlight_mentions(message, contacts)
    participant_items = []
    for person_id in sorted(person_ids):
        contact = contact_by_id.get(person_id)
        if contact is None:
            continue
        participant_items.append(
            f"<li>{html.escape(contact.display_name)} "
            f"(<code>{html.escape(person_id)}</code>)</li>"
        )
    mention_items = []
    for row in mention_rows:
        candidates = row["candidates"]  # type: ignore[index]
        candidate_text = "; ".join(
            f"{html.escape(item['person_id'])} score={item['score']} [{html.escape(item['reasons'])}]"
            for item in candidates
        ) or "no link candidates"
        mention_items.append(
            f"<tr><td>{html.escape(str(row['text']))}</td>"
            f"<td>{html.escape(str(row['label']))}</td>"
            f"<td>{html.escape(str(row['source']))}</td>"
            f"<td>{candidate_text}</td></tr>"
        )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Message {html.escape(message_id)}</title>
<style>
body {{ font-family: sans-serif; margin: 32px; background: #faf7ef; color: #1f2937; }}
.grid {{ display:grid; grid-template-columns: minmax(0, 2fr) minmax(320px, 1fr); gap: 24px; }}
.panel {{ background:#fffdf8; border:1px solid #e7e5e4; border-radius:14px; padding:20px 24px; }}
code {{ background:#f5f5f4; padding:2px 6px; border-radius:6px; }}
table {{ width:100%; border-collapse: collapse; }}
td, th {{ text-align:left; border-top:1px solid #e7e5e4; padding:8px 6px; vertical-align: top; }}
</style></head><body>
<p><a href="/?bundle={html.escape(bundle.name)}">Back</a> | <a href="/messages?bundle={html.escape(bundle.name)}">Interaction Explorer</a></p>
<h1>Interaction Explorer</h1>
<div class="grid">
  <div class="panel">
    <p><strong>Source:</strong> {html.escape(message.source)}<br>
    <strong>Timestamp:</strong> {html.escape(str(message.timestamp or ''))}<br>
    <strong>Sender:</strong> {html.escape(message.sender)}<br>
    <strong>Recipients:</strong> {html.escape(', '.join(message.recipients))}</p>
    <div style="line-height:1.7;">{highlight_html}</div>
  </div>
  <div class="panel">
    <h2>Explicit Participants</h2>
    <ul>{"".join(participant_items) or "<li>none</li>"}</ul>
    <h2>Extracted Mentions</h2>
    <table>
      <thead><tr><th>Text</th><th>Label</th><th>Source</th><th>Candidates</th></tr></thead>
      <tbody>{"".join(mention_items)}</tbody>
    </table>
  </div>
</div>
</body></html>"""


def render_messages_page(bundle: Path) -> str:
    _contacts, messages = load_bundle(bundle)
    rows = []
    for message in sorted(messages, key=lambda item: item.timestamp or datetime.min, reverse=True)[:100]:
        rows.append(
            "<tr>"
            f"<td><a href=\"/message?{urlencode({'bundle': bundle.name, 'message_id': message.message_id})}\">"
            f"{html.escape(message.subject or '(no subject)')}</a></td>"
            f"<td>{html.escape(message.source)}</td>"
            f"<td>{html.escape(str(message.timestamp or ''))}</td>"
            f"<td>{html.escape(message.sender)}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Interaction Explorer</title>
<style>
body {{ font-family: sans-serif; margin: 32px; background: #faf7ef; color: #1f2937; }}
.panel {{ max-width: 1200px; background:#fffdf8; border:1px solid #e7e5e4; border-radius:14px; padding:20px 24px; }}
table {{ width:100%; border-collapse: collapse; }}
td, th {{ text-align:left; border-top:1px solid #e7e5e4; padding:8px 6px; vertical-align: top; }}
</style></head><body>
<p><a href="/?bundle={html.escape(bundle.name)}">Back</a></p>
<div class="panel">
<h1>Interaction Explorer</h1>
<table>
  <thead><tr><th>Subject</th><th>Source</th><th>Timestamp</th><th>Sender</th></tr></thead>
  <tbody>{"".join(rows)}</tbody>
</table>
</div></body></html>"""


def render_person_page(bundle: Path, person_id: str) -> str:
    derived_dir = bundle / "derived"
    con = duckdb.connect()
    person_rows = con.execute(
        """
        SELECT person_name
        FROM read_json_auto(?)
        WHERE person_id = ?
          AND person_type = 'person'
        ORDER BY confidence DESC
        LIMIT 1
        """,
        [str(derived_dir / "person_message_edges.jsonl"), person_id],
    ).fetchall()
    person_name = person_rows[0][0] if person_rows else person_id
    rows = con.execute(
        """
        SELECT message_id, role, strongest_evidence_type, strongest_evidence_value, confidence, source
        FROM read_json_auto(?)
        WHERE person_id = ?
          AND person_type = 'person'
        ORDER BY confidence DESC, message_id DESC
        LIMIT 100
        """,
        [str(derived_dir / "person_message_edges.jsonl"), person_id],
    ).fetchall()
    items = []
    for message_id, role, evidence_type, evidence_value, confidence, source in rows:
        items.append(
            "<tr>"
            f"<td><a href=\"/message?{urlencode({'bundle': bundle.name, 'message_id': message_id})}\">{html.escape(message_id)}</a></td>"
            f"<td>{html.escape(role)}</td>"
            f"<td>{html.escape(str(source))}</td>"
            f"<td>{html.escape(str(evidence_type))}</td>"
            f"<td>{html.escape(str(evidence_value))}</td>"
            f"<td>{html.escape(str(confidence))}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>{html.escape(person_name)}</title>
<style>
body {{ font-family: sans-serif; margin: 32px; background: #faf7ef; color: #1f2937; }}
.panel {{ max-width: 1200px; background:#fffdf8; border:1px solid #e7e5e4; border-radius:14px; padding:20px 24px; }}
table {{ width:100%; border-collapse: collapse; }}
td, th {{ text-align:left; border-top:1px solid #e7e5e4; padding:8px 6px; vertical-align: top; }}
code {{ background:#f5f5f4; padding:2px 6px; border-radius:6px; }}
</style></head><body>
<p><a href="/?bundle={html.escape(bundle.name)}">Back</a></p>
<div class="panel">
<h1>Person Explorer</h1>
<p><strong>{html.escape(person_name)}</strong> <code>{html.escape(person_id)}</code></p>
<table>
  <thead><tr><th>Message</th><th>Role</th><th>Source</th><th>Evidence Type</th><th>Evidence</th><th>Confidence</th></tr></thead>
  <tbody>{"".join(items)}</tbody>
</table>
</div></body></html>"""


def render_index_html(base_dir: Path, selected_bundle: Path | None = None, notice: str | None = None) -> str:
    bundles = discover_bundles(base_dir)
    bundle = selected_bundle or (bundles[0] if bundles else None)
    people = list_people(bundle / "derived") if bundle and (bundle / "derived").exists() else []
    options = []
    for candidate in bundles:
        selected = " selected" if bundle and candidate == bundle else ""
        options.append(
            f'<option value="{html.escape(candidate.name)}"{selected}>{html.escape(candidate.name)}</option>'
        )
    people_options = []
    for person_id, person_name in people[:200]:
        people_options.append(
            f'<option value="{html.escape(person_id)}">{html.escape(person_name)} ({html.escape(person_id)})</option>'
        )
    notice_html = f'<p class="notice">{html.escape(notice)}</p>' if notice else ""
    selected_name = bundle.name if bundle else ""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Archive Graph Viewer</title>
  <style>
    body {{ font-family: sans-serif; margin: 32px; background: #faf7ef; color: #1f2937; }}
    .panel {{ max-width: 980px; background: #fffdf8; border: 1px solid #e7e5e4; border-radius: 14px; padding: 20px 24px; }}
    .row {{ display: flex; gap: 12px; flex-wrap: wrap; margin: 12px 0; }}
    label {{ font-weight: 600; display: block; margin-bottom: 6px; }}
    select, input {{ min-width: 320px; padding: 8px 10px; border: 1px solid #d6d3d1; border-radius: 8px; }}
    button, a.button {{ background: #1d4ed8; color: white; border: 0; border-radius: 8px; padding: 10px 14px; text-decoration: none; cursor: pointer; }}
    button.secondary, a.button.secondary {{ background: #57534e; }}
    .notice {{ background: #ecfccb; padding: 10px 12px; border-radius: 8px; }}
    code {{ background: #f5f5f4; padding: 2px 6px; border-radius: 6px; }}
  </style>
</head>
<body>
  <div class="panel">
    <h1>Archive Graph Viewer</h1>
    <p>Refresh derived tables and open the latest full-network or ego visualization without running shell commands.</p>
    {notice_html}
    <form method="post" action="/refresh">
      <label for="bundle">Bundle</label>
      <div class="row">
        <select id="bundle" name="bundle">{"".join(options)}</select>
        <button type="submit">Refresh Derived Tables</button>
      </div>
    </form>
    <div class="row">
      <a class="button" href="/graph?{urlencode({'bundle': selected_name})}">Open Full Graph</a>
      <a class="button" href="/messages?{urlencode({'bundle': selected_name})}">Interaction Explorer</a>
      <a class="button secondary" href="/">Reload Page</a>
    </div>
    <form method="get" action="/ego">
      <input type="hidden" name="bundle" value="{html.escape(selected_name)}">
      <label for="person_id">Ego Person</label>
      <div class="row">
        <input id="person_id" name="person_id" list="people" placeholder="Enter person_id">
        <datalist id="people">{"".join(people_options)}</datalist>
        <button type="submit">Open Ego Graph</button>
      </div>
    </form>
    <form method="get" action="/person">
      <input type="hidden" name="bundle" value="{html.escape(selected_name)}">
      <label for="person_id_explorer">Person Explorer</label>
      <div class="row">
        <input id="person_id_explorer" name="person_id" list="people" placeholder="Enter person_id">
        <button type="submit">Open Person Explorer</button>
      </div>
    </form>
    <p>Current bundle: <code>{html.escape(selected_name or 'none')}</code></p>
  </div>
</body>
</html>"""


def make_handler(base_dir: Path) -> type[BaseHTTPRequestHandler]:
    bundles = {bundle.name: bundle for bundle in discover_bundles(base_dir)}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            bundle = bundles.get(params.get("bundle", [""])[0])
            if parsed.path == "/":
                notice = params.get("notice", [""])[0] or None
                self._send_html(render_index_html(base_dir, bundle, notice))
                return
            if parsed.path == "/graph":
                if bundle is None:
                    self.send_error(HTTPStatus.BAD_REQUEST, "Unknown bundle")
                    return
                graph_path = base_dir / "analysis" / f"{bundle.name}_graph.html"
                render_graph(bundle / "derived", graph_path)
                self._send_file(graph_path)
                return
            if parsed.path == "/messages":
                if bundle is None:
                    self.send_error(HTTPStatus.BAD_REQUEST, "Unknown bundle")
                    return
                self._send_html(render_messages_page(bundle))
                return
            if parsed.path == "/message":
                message_id = params.get("message_id", [""])[0]
                if bundle is None or not message_id:
                    self.send_error(HTTPStatus.BAD_REQUEST, "Missing bundle or message_id")
                    return
                try:
                    self._send_html(render_message_page(bundle, message_id))
                except FileNotFoundError:
                    self.send_error(HTTPStatus.NOT_FOUND, "Unknown message_id")
                return
            if parsed.path == "/person":
                person_id = params.get("person_id", [""])[0]
                if bundle is None or not person_id:
                    self.send_error(HTTPStatus.BAD_REQUEST, "Missing bundle or person_id")
                    return
                self._send_html(render_person_page(bundle, person_id))
                return
            if parsed.path == "/ego":
                person_id = params.get("person_id", [""])[0]
                if bundle is None or not person_id:
                    self.send_error(HTTPStatus.BAD_REQUEST, "Missing bundle or person_id")
                    return
                ego_path = base_dir / "analysis" / f"{bundle.name}_{person_id}_ego.html"
                render_ego_graph(bundle / "derived", person_id, ego_path)
                self._send_file(ego_path)
                return
            self.send_error(HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path != "/refresh":
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            length = int(self.headers.get("Content-Length", "0"))
            data = parse_qs(self.rfile.read(length).decode("utf-8"))
            bundle = bundles.get(data.get("bundle", [""])[0])
            if bundle is None:
                self.send_error(HTTPStatus.BAD_REQUEST, "Unknown bundle")
                return
            build_edges(bundle)
            self.send_response(HTTPStatus.SEE_OTHER)
            self.send_header("Location", "/?" + urlencode({"bundle": bundle.name, "notice": "Derived tables refreshed"}))
            self.end_headers()

        def log_message(self, format: str, *args: object) -> None:  # noqa: A003
            return

        def _send_html(self, body: str) -> None:
            payload = body.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def _send_file(self, path: Path) -> None:
            payload = path.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    return Handler


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--base-dir", type=Path, default=Path.cwd())
    args = parser.parse_args()

    handler = make_handler(args.base_dir)
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"http://{args.host}:{args.port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
