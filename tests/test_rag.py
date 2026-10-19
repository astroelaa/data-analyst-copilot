from src.rag.store import citation, known_columns, load_entries


def test_all_columns_loaded():
    assert known_columns() == {
        "order_id", "order_date", "product", "category", "region",
        "quantity", "unit_price", "discount", "revenue",
    }


def test_entries_have_line_numbers():
    entries = load_entries()
    assert len(entries) == 9
    assert all(entry["line"] > 0 for entry in entries)


def test_citation_format():
    chunk = {"source": "data/data_dictionary.md", "line": 5, "column": "revenue"}
    assert citation(chunk) == "data/data_dictionary.md:L5 (revenue)"
