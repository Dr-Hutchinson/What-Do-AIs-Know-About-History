"""Challenge, source criticism, and recorded model comparisons."""
import json
import html
import os
from pathlib import Path
import random
import uuid

import streamlit as st

from history import LETTERS, SUBJECTS, csv_bytes, published_runs, questions, summaries
from experience import ISSUES, visitor_questions, split_question, session_json
from live import configuration, ensure_answer
from explorer import comparison_charts, model_card, model_lab

ARTICLE = "https://doi.org/10.5334/johd.489"
HELM = "https://crfm.stanford.edu/helm/mmlu/latest/"


def about():
    st.title("What does a correct answer tell us?")
    st.write("Test your historical knowledge alongside a language model—and examine what a benchmark score can tell us about either of you.")
    st.markdown(f"A companion to Daniel Hutchinson’s **[Benchmarking as Source Criticism: From Recognition to Reasoning in LLM Assessment]({ARTICLE})**, *Journal of Open Humanities Data* 12 (2026), 43.")
    st.markdown('### Can you outperform an AI on ten history questions?')
    st.write('Take the challenge, compare answers, then examine what the score actually measures.')
    if st.button('Take the history challenge', type='primary'):
        st.switch_page(st.session_state.navigation_pages['quiz'])
    st.subheader("One benchmark, three history subjects")
    st.write("MMLU—the Massive Multitask Language Understanding benchmark—includes multiple-choice questions in U.S., European, and World history. This project uses 606 test questions from those three subjects. Each offers four answer choices; uniform random guessing has an expected accuracy of 25%.")
    st.write("Choose Test yourself for a ten-question quiz. Model results & methods shows recorded assessments, individual answers, and the procedure used to produce them. Your quiz answers stay in your session and can be downloaded for your own review.")
    st.subheader("Recognition and historical reasoning")
    st.write("Selecting a correct answer demonstrates success on that question. It does not by itself establish the ability to weigh evidence, explain causation, or engage with historiographical debate. A high score here is not a measure of professional historical expertise.")
    with st.expander("Read the scores through the article’s four dimensions"):
        st.markdown("""
- **Contamination resistance:** These questions are public. A model may have encountered them during training; this experiment cannot determine whether it did.
- **Content diversity:** Three curricular subjects represent a limited selection of the past, not the full breadth of historical knowledge.
- **Format diversity:** Multiple-choice questions provide possible answers. This app does not assess open-ended synthesis.
- **Epistemological sophistication:** Agreement with an answer key does not test how a model weighs sources or constructs an interpretation.
""")
    st.markdown(f"For wider comparisons, explore [Stanford’s HELM MMLU leaderboard]({HELM}).")
    with st.expander("Project history and acknowledgements"):
        st.write("This project began in 2022 as an invitation for historians and the public to probe generative AI. This edition focuses on MMLU history assessment; the primary-source analyzer and Francis Bacon simulation have been retired.")
        st.write("Thanks to Abraham Gibson, William Mattingly, Patrick Wadden, and Ian Crowe for their contributions and feedback. The original project was supported by a sabbatical semester from Belmont Abbey College’s Office of Academic Affairs, with support from Provost Travis Feezell and Vice Provost David Williams.")


def run_label(run):
    return f"{run['config']['model']} · {run['created_at'][:10]} · {run['name']}"


def live_config():
    def get(key, default=None):
        value = os.environ.get(key)
        if value is not None:
            return value
        try:
            return st.secrets.get(key, default)
        except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
            return default
    return configuration(get)


def question_panel(q):
    source, stem = split_question(q['question'])
    st.caption(f"MMLU item · {q['id']}")
    if source:
        with st.container(border=True):
            st.caption('THE SOURCE')
            st.text(source)
    st.markdown(f"**{stem}**")


def comparison_strip(state, model_answers):
    cells = []
    for index, q in enumerate(state['questions']):
        answer = state['answers'].get(q['id'])
        record = model_answers.get(q['id'])
        color, label = '#e7e4dc', 'Unanswered'
        if answer:
            human_right = answer == q['answer']
            if record and record.get('status') != 'error':
                outcome = (human_right, record['correct'])
                color, label = {
                    (True, True): ('#127c70', 'Both matched the key'),
                    (False, False): ('#bd694c', 'Neither matched the key'),
                    (True, False): ('#305e9b', 'You alone matched the key'),
                    (False, True): ('#8858a0', 'Model alone matched the key'),
                }[outcome]
            else:
                color, label = ('#127c70', 'You matched the key') if human_right else ('#bd694c', 'You did not match the key')
                if record:
                    label += '; model request unavailable'
        cells.append(f'<div title="{html.escape(label)}" style="flex:1;min-width:24px;padding:12px 0;text-align:center;border-radius:8px;background:{color};color:{"#333" if not answer else "white"};font-weight:600">{index+1}</div>')
    st.markdown('<div style="display:flex;gap:6px;margin:12px 0" aria-label="Question outcomes">'+''.join(cells)+'</div>', unsafe_allow_html=True)
    st.caption('Teal: both match · Terracotta: neither · Blue: you alone · Purple: model alone. In solo mode, teal and terracotta show your result. Outcome labels are also available in the session review.')


def quiz():
    st.title('You versus the model')
    st.write('Ten questions. Lock in your answer, reveal the model’s choice, and ask what the result means.')
    runs, _ = published_runs()
    config = live_config()
    subject = st.selectbox('History subject', list(SUBJECTS), format_func=SUBJECTS.get, key='quiz_subject')
    modes = ['Solo practice']
    if runs:
        modes.insert(0, 'Recorded model')
    if config:
        modes.insert(0, 'Live open model')
    mode = st.selectbox('Choose your opponent', modes, key='opponent_mode')
    run = None
    if mode == 'Recorded model':
        selected = st.selectbox('Recorded model run', range(len(runs)), format_func=lambda i: run_label(runs[i]), key='quiz_model')
        run = runs[selected]
        opponent = {'mode': mode, 'model': run['config']['model'], 'run': run['name']}
        with st.expander('Meet your opponent'):
            model_card(run['config']['model'])
            st.caption(f"Saved assessment: {run_label(run)}. Five worked examples preceded each question.")
    elif mode == 'Live open model':
        opponent = {'mode': mode, 'model': config.model, 'provider': config.provider}
        with st.expander('Meet your opponent', expanded=True):
            model_card(config.model)
            st.caption('A fresh hosted response after you lock your answer. The model receives five worked examples, but neither your answer nor the test answer key.')
        st.caption('Live responses use a shared daily allowance. Your answers stay in this session; only the benchmark prompt goes to the model provider.')
    else:
        opponent = {'mode': mode}
        st.info('No model assessment has been published yet. You can take the quiz in solo mode.' if not runs else 'Practice with the benchmark key as your reference.')
    if not config:
        st.caption('Live open-model play is awaiting provider configuration. Recorded opponents appear after a complete assessment is published.')
    excluded = sum(q['id'] in ISSUES for q in questions(subject))
    st.caption(f'Visitor selection: {len(visitor_questions(subject))} eligible items · {excluded} reviewed passage mismatches excluded. Full model assessments retain all canonical rows.')
    identity = (subject, json.dumps(opponent, sort_keys=True))
    state = st.session_state.get('quiz_state')
    restart = st.button('Start a new quiz')
    if state is None or state['identity'] != identity or restart:
        state = {'identity': identity, 'questions': random.sample(visitor_questions(subject), 10),
                 'answers': {}, 'model_answers': {}, 'reflections': {}, 'index': 0,
                 'nonce': uuid.uuid4().hex, 'opponent': opponent}
        st.session_state.quiz_state = state
    model_answers = {r['id']: r for r in run['records']} if run else state['model_answers']
    answered = state['answers']
    completed = [q for q in state['questions'] if q['id'] in answered]
    human_score = sum(answered[q['id']] == q['answer'] for q in completed)
    left, right = st.columns(2)
    left.metric('Your score', f'{human_score} / {len(completed)}')
    if mode != 'Solo practice':
        available = [model_answers[q['id']] for q in completed if q['id'] in model_answers and model_answers[q['id']].get('status') != 'error']
        right.metric('Model on the same questions', f"{sum(r['correct'] for r in available)} / {len(available)}")
        failures = sum(q['id'] in model_answers and model_answers[q['id']].get('status') == 'error' for q in completed)
        if failures:
            st.caption(f'{failures} model request(s) unavailable; excluded from this live comparison. This is not a published benchmark score.')
    st.progress(len(completed) / 10, text=f'{len(completed)} of 10 answered')
    comparison_strip(state, model_answers)
    if state['index'] >= 10:
        st.success('Quiz complete')
        st.subheader('What did your score measure?')
        st.write('You selected answers from a public, curricular benchmark. This short challenge does not establish historical expertise or distinguish memorization from reasoning.')
        if mode != 'Solo practice':
            matched = [q for q in completed if q['id'] in model_answers and model_answers[q['id']].get('status') != 'error']
            you_only = sum(answered[q['id']] == q['answer'] and not model_answers[q['id']]['correct'] for q in matched)
            model_only = sum(answered[q['id']] != q['answer'] and model_answers[q['id']]['correct'] for q in matched)
            st.write(f'On {len(matched)} comparable questions, you alone matched the key on {you_only}; the model alone matched it on {model_only}.')
        review = []
        for q in state['questions']:
            row = {'ID': q['id'], 'Question': q['question'], 'Your answer': answered[q['id']], 'Official key': q['answer'], 'You matched': answered[q['id']] == q['answer']}
            record = model_answers.get(q['id'])
            if record:
                row['Model answer'] = 'Unavailable' if record.get('status') == 'error' else record['answer'] or 'Invalid'
            review.append(row)
        st.dataframe(review, hide_index=True, use_container_width=True)
        if st.button('Question the benchmark', type='primary'):
            st.switch_page(st.session_state.navigation_pages['critique'])
        if st.button('Explore model performance'):
            st.switch_page(st.session_state.navigation_pages['results'])
    else:
        q = state['questions'][state['index']]
        st.subheader(f"Question {state['index'] + 1}")
        question_panel(q)
        if q['id'] not in answered:
            with st.form(f"answer_{state['nonce']}_{state['index']}"):
                choice = st.radio('Your answer', list(LETTERS), index=None,
                                  format_func=lambda letter: f"{letter}. {q['options'][LETTERS.index(letter)]}")
                submitted = st.form_submit_button('Submit answer', type='primary')
            if submitted:
                if choice is None:
                    st.warning('Choose an answer first.')
                else:
                    answered[q['id']] = choice
                    st.rerun()
        else:
            if mode == 'Live open model' and q['id'] not in state['model_answers']:
                with st.spinner('Your answer is locked. The model is answering the same question…'):
                    ensure_answer(state, q, config, Path(__file__).parent / '.live/allowance.json')
                st.rerun()
            chosen = answered[q['id']]
            record = model_answers.get(q['id'])
            columns = st.columns(3)
            with columns[0].container(border=True):
                st.caption('YOU')
                st.subheader(chosen)
                st.write('Matches key' if chosen == q['answer'] else 'Does not match key')
            with columns[1].container(border=True):
                st.caption('THE MODEL')
                st.subheader('—' if not record or record.get('status') == 'error' else record['answer'] or 'Invalid')
                st.write('Solo practice' if not record else 'Unavailable' if record.get('status') == 'error' else 'Matches key' if record['correct'] else 'Does not match key')
            with columns[2].container(border=True):
                st.caption('BENCHMARK KEY')
                st.subheader(q['answer'])
                st.write(q['options'][LETTERS.index(q['answer'])])
            if chosen == q['answer']:
                st.success(f'Correct. You chose {chosen}.')
            else:
                st.error(f"You chose {chosen}. The official answer is {q['answer']}.")
            with st.expander('Review all answer choices'):
                for letter, text in zip(LETTERS, q['options']):
                    st.write(f'{letter}. {text}')
            if record:
                if record.get('status') == 'error':
                    st.warning(record['reason'])
                else:
                    with st.expander('See the recorded model response'):
                        st.code(record['raw'] or '(empty response)')
                        st.caption(f"Response model: {record.get('response_model', opponent.get('model'))}")
                        if 'latency_seconds' in record:
                            st.caption(f"Response time: {record['latency_seconds']} seconds")
                        if 'messages' in record:
                            st.json(record['messages'])
            reflection = st.radio('What helped you answer?', ['Select a reflection', 'Evidence in the passage', 'Prior historical knowledge', 'The answer choices', 'A guess / uncertainty'], key=f"reflection_{state['nonce']}_{q['id']}")
            if reflection != 'Select a reflection':
                state['reflections'][q['id']] = reflection
            st.caption('Reflection is optional and unscored. A correct choice alone does not tell us how an answer was reached.')
            def advance():
                state['index'] += 1
            st.button('See final score' if state['index'] == 9 else 'Next question', type='primary', on_click=advance)
    export_state = {**state, 'model_answers': {q['id']: model_answers[q['id']] for q in state['questions'] if q['id'] in model_answers}}
    st.download_button('Download this session', session_json(export_state), 'history-challenge.json', 'application/json')


def critique():
    st.title('Question the benchmark')
    st.write('A score depends on the questions and the key. Can you identify a problem in this canonical MMLU item?')
    q = questions('high_school_us_history')[129]
    question_panel(q)
    for letter, option in zip(LETTERS, q['options']):
        st.write(f'{letter}. {option}')
    st.caption('This exhibit is unscored and excluded from the ordinary visitor challenge.')
    st.radio('Does the supplied passage support this question?', ['Choose an observation', 'Yes, it supplies the relevant context', 'No, the passage and question concern different contexts', 'I am unsure'], key='source_observation')
    if st.button('Reveal the source problem'):
        st.session_state.source_revealed = True
    if st.session_state.get('source_revealed'):
        st.warning(ISSUES[q['id']]['explanation'])
        st.write('The official key is A: British forts in the Great Lakes. An answer can agree with that key while bypassing the unrelated passage entirely. This exposes a problem in the assessment itself.')
        st.write('We downloaded the original archive again and compared all six history CSVs byte for byte: 606 test questions and 15 development examples match. This defect is upstream, and appears in U.S. test rows 22, 44, and 130.')
        st.markdown('[Original MMLU dataset and evaluation project](https://github.com/hendrycks/test)')
        st.download_button('Download the validation report', (Path(__file__).parent / 'data/VALIDATION_2026-09-30.md').read_text(), 'mmlu-validation.md', 'text/markdown')
    st.subheader('Four ways to read a score')
    tabs = st.tabs(['Training exposure', 'Whose history?', 'Recognition / reasoning', 'How do we know?'])
    with tabs[0]:
        st.write('Public questions may have appeared in training data. Correct answers do not establish whether a model memorized an item. Rewording a public question does not make it demonstrably uncontaminated.')
    with tabs[1]:
        st.write('MMLU history reflects a particular curriculum. Selecting World History does not provide evenly balanced coverage of the world’s regions, languages, or historical societies.')
    with tabs[2]:
        st.write('Four supplied choices scaffold recognition. Explaining a causal relationship or synthesizing conflicting sources demands a different assessment. A generated explanation after a correct answer does not prove how the original answer was produced.')
    with tabs[3]:
        st.write('Ask whether the source supports the claim, whether the question is coherent, and whether the key is defensible. The benchmark deserves the same scrutiny as the model.')
    st.markdown(f'Read the framework in [Benchmarking as Source Criticism]({ARTICLE}).')


def results():
    st.title("Model results & methods")
    st.write("Recorded performance on three MMLU history subjects. These are project evaluations, not full 57-subject MMLU scores or Stanford HELM reproductions.")
    runs, problems = published_runs()
    comparison_charts(runs)
    if problems:
        st.warning("Some result files could not be validated and are excluded from comparisons.")
        with st.expander("Result validation details"):
            st.write(problems)
    if not runs:
        st.info("No completed model assessments have been published yet. The evaluation method is described below.")
    else:
        table = []
        for run in runs:
            for row in summaries(run["records"]):
                table.append({"Model / run": run_label(run), **row})
        st.dataframe(table, hide_index=True, use_container_width=True)
        selected = st.selectbox("Inspect a run", range(len(runs)), format_func=lambda i: run_label(runs[i]))
        run = runs[selected]
        st.caption(f"Recorded {run['created_at']} through {run.get('updated_at', run['created_at'])}. One response per question; uniform random guessing baseline: 25%.")
        subject = st.selectbox("Filter subject", ["All subjects", *SUBJECTS], format_func=lambda s: SUBJECTS.get(s, s))
        wrong_only = st.checkbox("Show unsuccessful answers only")
        records = [r for r in run["records"] if (subject == "All subjects" or r["subject"] == subject) and (not wrong_only or not r["correct"])]
        st.dataframe([{"ID": r["id"], "Question": r["question"], "Model": r["answer"] or "Invalid", "Official answer": r["expected"], "Correct": r["correct"]} for r in records], hide_index=True, use_container_width=True)
        if records:
            item = st.selectbox("Inspect question and exact prompt", range(len(records)), format_func=lambda i: records[i]["id"])
            record = records[item]
            with st.expander("Question, answer options, prompt and raw response"):
                st.write(record["question"])
                for letter, option in zip(LETTERS, record["options"]):
                    st.write(f"{letter}. {option}")
                st.json(record["messages"])
                st.code(record["raw"] or "(empty response)")
                st.write(f"Response model: {record.get('response_model', 'Unspecified')}; finish reason: {record.get('finish_reason', 'Unspecified')}")
        st.download_button("Download all answers (CSV)", csv_bytes(run["records"]), f"{run['name']}-answers.csv", "text/csv")
        st.download_button("Download full run and prompts (JSON)", json.dumps(run, indent=2), f"{run['name']}-run.json", "application/json")
        with st.expander("Run configuration"):
            st.json(run["config"])
    model_lab()
    st.subheader("How the assessment works")
    st.markdown("""
1. **Fixed data:** 204 U.S., 165 European, and 237 World history test questions from the original MMLU archive. The source and file checksums are preserved with the project.
2. **Five examples:** Each request contains all five worked development examples for its subject, then one test question with its four choices. The test answer is withheld. Each request is independent; no browsing or retrieval is supplied.
3. **One answer:** The model is asked for a single letter. Scoring strips surrounding whitespace and accepts upper- or lower-case A–D. Explanations, ambiguous answers, and empty responses are invalid and count as unsuccessful.
4. **Transparent results:** Accuracy is correct answers divided by all test questions in that subject, including invalid responses. API failures leave a run incomplete; it cannot enter the public comparison. Small smoke runs are also excluded.
5. **A recorded experiment:** Model ID, dates, settings, prompts, raw responses, and scoring decisions are downloadable. A single run does not measure repeat-run stability. Settings and model versions matter when comparing results.
""")
    st.subheader("What the scores cannot establish")
    st.write("Public benchmark questions may have appeared in training data. These results cannot distinguish memorization from generalization. They cover a limited curriculum and answer-selection task, not source criticism or interpretive synthesis. A ten-question visitor quiz is not included in the benchmark results.")
    st.markdown(f"Read the [accompanying article]({ARTICLE}), inspect the [original MMLU project](https://github.com/hendrycks/test), or explore [Stanford’s HELM MMLU leaderboard]({HELM}). Stanford’s [published methodology](https://crfm.stanford.edu/2024/05/01/helm-mmlu.html) motivates our emphasis on transparent prompts and responses; exact protocols and scores may differ.")
