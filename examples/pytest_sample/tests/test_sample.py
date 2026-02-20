from pyrep.runtime import attach, set_env, set_label, step


def test_login_flow():
    set_env("target", "staging")
    set_label("component", "auth")
    with step("Open login page"):
        pass
    with step("Submit credentials"):
        attach("request.json", '{"username": "demo"}', mime="application/json")
    assert True


def test_fails_example():
    with step("Broken action"):
        assert 1 == 2
