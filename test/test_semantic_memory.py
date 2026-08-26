from src.semantic_memory import SemanticMemory


def test_semantic_memory_add_search_and_update():
    memory = SemanticMemory()

    memory.add(
        key="report_currency",
        value="CLP",
        metadata={
            "customer_id": "customer_001",
        },
    )

    memory.add(
        key="report_currency",
        value="USD",
        metadata={
            "customer_id": "customer_002",
        },
    )

    results = memory.search(
        query="currency",
        metadata={
            "customer_id": "customer_001",
        },
    )

    assert len(results) == 1

    assert (
        results[0].value
        == "CLP"
    )

    memory.update(
        key="report_currency",
        value="EUR",
        metadata={
            "customer_id": "customer_001",
        },
    )

    updated_results = memory.search(
        query="currency",
        metadata={
            "customer_id": "customer_001",
        },
    )

    assert len(updated_results) == 1

    assert (
        updated_results[0].value
        == "EUR"
    )


def test_semantic_memory_update_adds_when_missing():
    memory = SemanticMemory()

    memory.update(
        key="report_format",
        value="PDF",
        metadata={
            "customer_id": "customer_001",
        },
    )

    entries = memory.list_entries()

    assert len(entries) == 1

    assert entries[0].key == "report_format"

    assert entries[0].value == "PDF"