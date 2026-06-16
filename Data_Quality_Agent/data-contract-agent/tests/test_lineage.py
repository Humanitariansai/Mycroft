def test_amount_usd_traces_to_amount_cents(index):
    assert index.column_footprint[("stg_subscriptions", "amount_usd")] == {
        ("subscriptions", "amount_cents")
    }


def test_mrr_amount_traces_through_staging(index):
    fp = index.column_footprint[("fct_mrr", "monthly_amount_usd")]
    assert ("subscriptions", "amount_cents") in fp


def test_models_reading_signup_date_is_transitive(index):
    assert index.models_reading("users", "signup_date") == [
        "stg_users",
        "dim_users",
        "fct_engagement",
    ]


def test_models_reading_amount_cents(index):
    assert index.models_reading("subscriptions", "amount_cents") == [
        "stg_subscriptions",
        "fct_mrr",
    ]


def test_enum_filter_detected_on_fct_mrr(index):
    filters = index.enum_filters_by_model.get("fct_mrr", [])
    assert any(
        set(f.values) == {"active", "trialing"}
        and (f.source_table, f.source_column) == ("subscriptions", "status")
        for f in filters
    )


def test_no_false_lineage_for_unrelated_column(index):
    # nothing reads users.phone (it doesn't exist downstream)
    assert index.models_reading("users", "phone") == []
