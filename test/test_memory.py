from src.memory import Memory


def test_memory_set_and_get():
    memory = Memory()

    memory.set(
        "name",
        "Sebastian",
    )

    assert memory.get("name") == "Sebastian"


def test_memory_missing_value():
    memory = Memory()

    assert memory.get("unknown") is None


def test_memory_all():
    memory = Memory()

    memory.set(
        "name",
        "Sebastian",
    )

    memory.set(
        "project",
        "AI data assistant",
    )

    result = memory.all()

    assert result == {
        "name": "Sebastian",
        "project": "AI data assistant",
    }