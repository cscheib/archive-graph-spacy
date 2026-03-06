from spacy.lang.en import English
from spacy.tokens import Span

from archive_graph_spacy import build_blank_ner_pipeline, extract_entities


def test_build_blank_ner_pipeline_adds_ner_component() -> None:
    nlp = build_blank_ner_pipeline()

    assert nlp.lang == "en"
    assert "ner" in nlp.pipe_names


def test_extract_entities_returns_text_and_labels() -> None:
    nlp = English()
    doc = nlp.make_doc("Ada Lovelace visited London.")
    doc.ents = [Span(doc, 0, 2, label="PERSON"), Span(doc, 3, 4, label="GPE")]

    assert extract_entities(doc) == [
        ("Ada Lovelace", "PERSON"),
        ("London", "GPE"),
    ]
