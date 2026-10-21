"""Interactive charts built only from verified complete project runs."""
import json
from pathlib import Path
import plotly.graph_objects as go
import streamlit as st
from history import SUBJECTS, questions
from experience import ISSUES

CATALOG = json.loads((Path(__file__).parent / 'models.json').read_text())


def catalog_id(model):
    # HF's provider suffix selects a route, not a different model's weights.
    canonical = model.split(':', 1)[0]
    return 'Qwen/Qwen3-8B' if canonical == 'qwen/qwen3-8b' else canonical


def model_card(model):
    canonical = catalog_id(model)
    metadata = CATALOG.get(canonical)
    if not metadata:
        st.write(f'**{model}**')
        st.caption('Size and training details have not been documented for this model. No size is inferred from its name.')
        return
    st.write(f"**{metadata['name']}** · {metadata['creator']}")
    st.caption(f"{metadata['total_parameters_b']:g}B total parameters · {metadata['architecture']} · {metadata['license']}")
    st.write(metadata['training'])
    st.markdown(f"[Developer model card]({metadata['source']})")


def model_lab():
    st.subheader('Meet the models')
    st.write('Explore disclosed model sizes before comparing their scores. These are model-card facts, not evaluation results.')
    models = sorted(CATALOG, key=lambda m: CATALOG[m]['total_parameters_b'])
    figure = go.Figure(go.Bar(x=[CATALOG[m]['name'] for m in models],
                             y=[CATALOG[m]['total_parameters_b'] for m in models],
                             marker_color='#127c70', customdata=models,
                             hovertemplate='%{x}<br>%{y} billion total parameters<extra></extra>'))
    figure.update_layout(yaxis_title='Disclosed parameters (billions)', height=300)
    st.plotly_chart(figure, use_container_width=True)
    selected = st.selectbox('Inspect a model card', models, format_func=lambda m: CATALOG[m]['name'])
    with st.container(border=True):
        model_card(selected)
    st.caption('These models belong to one family, but size is only one variable. Hosted availability and the exact inference settings must be verified before testing.')


def comparison_charts(runs):
    if not runs:
        st.info('The comparison explorer is ready for verified model assessments. No completed runs are available yet; charts will appear here after evaluation.')
        st.write('Planned comparisons: accuracy by subject, disagreement on individual questions, and performance against disclosed model size.')
        return
    labels = [f"{r['config']['model']} · {r['name']}" for r in runs]
    accuracy = go.Figure()
    for run, label in zip(runs, labels):
        values = []
        for subject in SUBJECTS:
            records = [r for r in run['records'] if r['subject'] == subject]
            values.append(100 * sum(r['correct'] for r in records) / len(records))
        accuracy.add_trace(go.Bar(name=label, x=list(SUBJECTS.values()), y=values))
    accuracy.add_hline(y=25, line_dash='dot', annotation_text='Uniform random choice: 25%')
    accuracy.update_layout(yaxis_title='Canonical test accuracy (%)', yaxis_range=[0, 100], barmode='group', height=390)
    st.plotly_chart(accuracy, use_container_width=True)
    st.caption('Full canonical test sets, including known defective items. These runs share our five-shot prompts; provider, token budget, sampling, and reasoning settings can differ and remain inspectable below.')
    settings = [{
        'Run': label, 'Provider': run['config'].get('provider', 'Unspecified'),
        'Token budget': run['config'].get('max_completion_tokens'),
        'Temperature': run['config'].get('temperature') if run['config'].get('temperature') is not None else 'Provider default',
        'Reasoning effort': run['config'].get('reasoning_effort') or 'Provider default',
        'Invalid outputs': sum(r['status'] == 'invalid' for r in run['records']),
        'Output limit reached': sum(r.get('finish_reason') == 'length' for r in run['records']),
        'Non-letter text (not truncated)': sum(r['status'] == 'invalid' and bool(r['raw'].strip()) and r.get('finish_reason') != 'length' for r in run['records']),
        'Date': run['created_at'][:10],
    } for run, label in zip(runs, labels)]
    with st.expander('Compare inference settings before interpreting score differences'):
        st.table(settings)
        st.caption('Invalid outputs remain in the accuracy denominator. A response that reaches its output limit may contain no final letter. The 4B Instruct 2507 release supports only non-thinking mode; the original 8B, 14B, and 32B releases can spend output tokens on thinking. These differences prevent attributing score changes to size alone.')

    subject = st.selectbox('Subject for disagreement explorer', list(SUBJECTS), format_func=SUBJECTS.get)
    items = questions(subject)
    start = st.slider('First canonical row in the matrix', 1, len(items), 1)
    window = items[start-1:start+19]
    grid = go.Figure()
    colors = {True: '#127c70', False: '#bd694c'}
    for row_index, (run, label) in enumerate(zip(runs, labels)):
        records = {r['id']: r for r in run['records']}
        grid.add_trace(go.Scatter(x=[int(q['id'].split(':')[-1]) for q in window], y=[label]*len(window),
            mode='markers', marker={'symbol': 'square', 'size': 23, 'color': [colors[records[q['id']]['correct']] for q in window]},
            customdata=[[q['id'], row_index, records[q['id']]['answer'] or 'Invalid', q['answer']] for q in window],
            hovertemplate='%{customdata[0]}<br>Model: %{customdata[2]} · Key: %{customdata[3]}<extra></extra>', showlegend=False))
    grid.update_layout(height=max(240, 80 + len(runs)*50), xaxis_title='Canonical row — select a square to inspect', clickmode='event+select')
    event = st.plotly_chart(grid, use_container_width=True, on_select='rerun', key='disagreement_chart')
    st.caption('Teal: matches key · Terracotta: incorrect or invalid. All runs shown use the same questions.')
    selected_id = window[0]['id']
    selected_run = 0
    points = event.selection.points
    if points:
        selected_id, selected_run = points[0]['customdata'][:2]
    record = next(r for r in runs[int(selected_run)]['records'] if r['id'] == selected_id)
    with st.expander(f'Inspect {selected_id}', expanded=bool(points)):
        if selected_id in ISSUES:
            st.warning(ISSUES[selected_id]['explanation'])
        st.write(record['question'])
        for letter, option in zip('ABCD', record['options']):
            st.write(f'{letter}. {option}')
        st.write(f"Model answer: {record['answer'] or 'Invalid'} · Official key: {record['expected']}")
        st.code(record['raw'] or '(empty response)')

    st.subheader('Does a larger model always do better?')
    points_by_model = []
    unknown = []
    for run, label in zip(runs, labels):
        model = run['config']['model']
        metadata = CATALOG.get(catalog_id(model))
        if not metadata or not metadata.get('total_parameters_b'):
            unknown.append(label)
            continue
        points_by_model.append((label, metadata, 100*sum(r['correct'] for r in run['records'])/len(run['records'])))
    if points_by_model:
        fig = go.Figure(go.Scatter(x=[p[1]['total_parameters_b'] for p in points_by_model], y=[p[2] for p in points_by_model],
                                  mode='markers', text=[p[0] for p in points_by_model], marker={'size': 15},
                                  hovertemplate='%{text}<br>%{x}B total parameters · %{y:.1f}%<extra></extra>'))
        fig.update_layout(xaxis_title='Disclosed total parameters (billions)', xaxis_type='log', yaxis_title='All-history accuracy (%)', yaxis_range=[0,100])
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info('No evaluated model has documented parameter counts yet.')
    if unknown:
        st.caption('Undisclosed or undocumented size: ' + '; '.join(unknown))
    st.write('Size alone does not establish the cause of a score difference. Compare model families, training disclosures, and inference settings. Total and active parameters differ for mixture-of-experts models.')
