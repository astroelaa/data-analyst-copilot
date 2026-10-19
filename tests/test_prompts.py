from src.prompts import build_fix_prompt, build_plan_prompt


def test_plan_prompt_defines_role_and_analysis_constraints():
    prompt = build_plan_prompt("Compare revenue by region", "region: sales region")
    assert "careful English-language data analyst" in prompt
    assert "Preserve every filter, date range, category, region, metric, grouping, ranking, and comparison" in prompt
    assert "Never invent, rename, or substitute a column" in prompt
    assert "region: sales region" in prompt


def test_fix_prompt_preserves_requested_analysis():
    prompt = build_fix_prompt(
        "What was revenue in Cairo in January?",
        "result = df['revenue'].sum()",
        "missing filter",
        ["region", "order_date", "revenue"],
    )
    assert "without changing the requested analysis" in prompt
    assert "Preserve every requested filter, date range, metric, grouping, comparison, and ranking" in prompt
