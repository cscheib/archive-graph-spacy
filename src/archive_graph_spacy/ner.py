"""Minimal helpers for spaCy NER setup."""

from __future__ import annotations

import spacy
from spacy.language import Language
from spacy.tokens import Doc


def build_blank_ner_pipeline(language_code: str = "en") -> Language:
    """Create a blank spaCy pipeline with an NER component."""
    nlp = spacy.blank(language_code)
    if "ner" not in nlp.pipe_names:
        nlp.add_pipe("ner")
    return nlp


def extract_entities(doc: Doc) -> list[tuple[str, str]]:
    """Return entity text and label pairs from a processed Doc."""
    return [(ent.text, ent.label_) for ent in doc.ents]
