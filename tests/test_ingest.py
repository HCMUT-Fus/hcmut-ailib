from src.ingest import normalize_records


def test_normalize_records_fills_missing_fields():
    data = [{"title": "  A title  "}]
    normalized = normalize_records(data)

    assert normalized == [
        {
            "title": "A title",
            "abstract": "",
            "authors": [],
            "doi": "",
        }
    ]
