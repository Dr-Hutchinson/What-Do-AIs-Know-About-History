from streamlit.testing.v1 import AppTest


def button(app, label):
    return next(b for b in app.button if b.label == label)


def test_entry_and_results_without_secrets(monkeypatch):
    import views
    monkeypatch.setattr(views, 'published_runs', lambda: ([], []))
    app = AppTest.from_file('app.py').run()
    assert not app.exception
    assert 'correct answer' in app.title[0].value
    result = AppTest.from_string('from views import results; results()').run()
    assert not result.exception
    assert 'No completed' in result.info[0].value


def test_quiz_submission_navigation_and_subject_reset():
    app = AppTest.from_string('from views import quiz; quiz()').run()
    assert not app.exception
    state = app.session_state['quiz_state']
    original_id = state['questions'][0]['id']
    answer = state['questions'][0]['answer']
    assert len(app.success) == 0
    button(app, 'Submit answer').click().run()
    assert app.warning[0].value == 'Choose an answer first.'
    assert app.session_state['quiz_state']['questions'][0]['id'] == original_id
    app.radio[0].set_value(answer)
    button(app, 'Submit answer').click().run()
    assert app.metric[0].value == '1 / 1'
    assert 'Correct' in app.success[0].value
    app.run()
    assert app.metric[0].value == '1 / 1'
    button(app, 'Next question').click().run()
    assert app.session_state['quiz_state']['index'] == 1
    assert app.radio[0].value is None
    app.selectbox[0].set_value('high_school_world_history').run()
    assert app.session_state['quiz_state']['index'] == 0
    assert app.metric[0].value == '0 / 0'
    assert all(q['subject'] == 'high_school_world_history' for q in app.session_state['quiz_state']['questions'])
    for index in range(10):
        answer = app.session_state['quiz_state']['questions'][index]['answer']
        app.radio[0].set_value(answer)
        button(app, 'Submit answer').click().run()
        button(app, 'See final score' if index == 9 else 'Next question').click().run()
    assert app.metric[0].value == '10 / 10'
    assert not app.exception
    button(app, 'Start a new quiz').click().run()
    assert app.metric[0].value == '0 / 0'


def test_recorded_comparison_and_results(monkeypatch):
    import views
    from test_history import make_full_run
    run = make_full_run()
    run['name'] = 'temporary-test-fixture'
    monkeypatch.setattr(views, 'published_runs', lambda: ([run], []))
    app = AppTest.from_string('from views import quiz; quiz()').run()
    assert not app.exception
    assert len(app.metric) == 2
    assert len(app.code) == 0  # Model response is hidden until submission.
    q = app.session_state['quiz_state']['questions'][0]
    app.radio[0].set_value(q['answer'])
    button(app, 'Submit answer').click().run()
    assert app.metric[0].value == '1 / 1'
    assert app.metric[1].value == f"{int(q['answer'] == 'A')} / 1"
    assert app.code[0].value == 'A'
    result = AppTest.from_string('from views import results; results()').run()
    assert not result.exception
    assert len(result.dataframe[0].value) == 3
    result.checkbox[0].check().run()
    assert not result.exception
    assert not result.dataframe[1].value['Correct'].any()
