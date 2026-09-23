from src.search_engine import search


def test_search_ranks_most_relevant_record_first():
    records = [
        {"title": "Neural networks", "abstract": "deep learning models"},
        {"title": "Classical mechanics", "abstract": "newtonian physics"},
    ]

    result = search("deep learning", records, top_k=1)

    assert result[0]["record"]["title"] == "Neural networks"
