"""
Observability tests.

Verify:
1. Successful tool execution is summarized.
2. Failures are classified without leaking error details.
3. Sensitive tool arguments are not included in reports.
"""

from types import SimpleNamespace

from production.observability import build_execution_report


def test_successful_execution_report():
    result = SimpleNamespace(
        new_items=[
            SimpleNamespace(
                raw_item=SimpleNamespace(
                    type="function_call",
                    name="get_customer_balance",
                    arguments='{"customer_id":"customer_001"}',
                )
            )
        ]
    )

    report = build_execution_report(result)

    assert report.status == "completed"
    assert report.tool_names == ("get_customer_balance",)
    assert report.tool_call_count == 1
    assert report.error_type is None

    # Tool arguments must not appear in the report.
    assert "customer_001" not in str(report)


def test_failed_execution_report():
    error = RuntimeError(
        "Database failure involving customer_001"
    )

    report = build_execution_report(error=error)

    assert report.status == "failed"
    assert report.error_type == "RuntimeError"
    assert report.tool_call_count == 0

    # Never include raw exception messages.
    assert "customer_001" not in str(report)


def test_missing_result_is_rejected():
    try:
        build_execution_report()
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Expected ValueError for missing execution result."
        )