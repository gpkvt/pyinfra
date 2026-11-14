"""VSCodium task regression tests."""

def test_vscodium_skips_installed_extension_query_for_empty_list(
    pyinfra_task_harness, monkeypatch,
):
    """An empty extension list must not query whether VSCodium is installed."""
    def unexpected_fact(*_args, **_kwargs):
        raise AssertionError("No installed-extension query is needed")

    monkeypatch.setattr(
        pyinfra_task_harness.host,
        "get_fact",
        unexpected_fact,
    )
    pyinfra_task_harness.load("vscodium.py", {
        "username": "tester",
        "vscodium": {"extensions": []},
    })

    assert not any(
        namespace == "server" and name == "shell"
        for namespace, name, _kwargs in pyinfra_task_harness.calls
    )
