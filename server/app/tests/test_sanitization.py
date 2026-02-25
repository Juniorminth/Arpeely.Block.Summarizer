from server.app.services.summarizer.agent.summarizer_agent import SummarizerAgentOpenAI


def make_agent():
    """Returns a real agent instance without triggering LLM init."""
    instance = object.__new__(SummarizerAgentOpenAI)
    return instance


def test_clean_text_does_not_need_sanitization():
    a = make_agent()
    assert not a._needs_sanitization("Hello, this is a clean sentence!")


def test_html_tags_trigger_sanitization():
    a = make_agent()
    assert a._needs_sanitization("<div>Some content</div>")


def test_html_entities_trigger_sanitization():
    a = make_agent()
    assert a._needs_sanitization("Hello &amp; welcome")


def test_url_triggers_sanitization():
    a = make_agent()
    assert a._needs_sanitization("Visit https://example.com for more")


def test_standard_punctuation_does_not_trigger():
    a = make_agent()
    assert not a._needs_sanitization("Hello! How are you? I'm fine: great.")


def test_non_ascii_unicode_letters_do_not_trigger_sanitization():
    a = make_agent()
    assert not a._needs_sanitization("Héllo wörld")


def test_em_dash_does_not_trigger_sanitization():
    a = make_agent()
    # Real prose from a page — em dash should never route to sanitization
    assert not a._needs_sanitization("Bridger Bowl — community-owned and fiercely independent.")


def test_en_dash_does_not_trigger_sanitization():
    a = make_agent()
    assert not a._needs_sanitization("Open Monday–Friday, 9am–5pm.")


def test_smart_quotes_do_not_trigger_sanitization():
    a = make_agent()
    assert not a._needs_sanitization("It\u2019s a \u201cserious\u201d mountain.")


def test_ellipsis_does_not_trigger_sanitization():
    a = make_agent()
    assert not a._needs_sanitization("More to come\u2026")


