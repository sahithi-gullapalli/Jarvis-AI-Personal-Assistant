import jarvis_actions


def test_travel_question_does_not_trigger_time():
    assert jarvis_actions.try_action(
        "what is the best time to visit Japan"
    ) is None


def test_resume_question_does_not_trigger_date():
    assert jarvis_actions.try_action(
        "update my resume"
    ) is None


def test_supermarket_does_not_trigger_market():
    assert jarvis_actions.try_action(
        "supermarket near me"
    ) is None


def test_explicit_time_request_is_recognized():
    assert jarvis_actions._is_time_request("what time is it")


def test_explicit_date_request_is_recognized():
    assert jarvis_actions._is_date_request(
        "what is today's date"
    )


def test_market_keyword_uses_word_boundaries():
    assert not jarvis_actions._is_market_request("supermarket")
    assert jarvis_actions._is_market_request("stock market")