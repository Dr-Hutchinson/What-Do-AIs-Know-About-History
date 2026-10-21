"""Visitor curation and downloadable session records; canonical data stays unchanged."""
import json
from history import questions

ISSUES = {
    f'high_school_us_history:test:{row:03}': {
        'kind': 'Passage / question mismatch',
        'explanation': 'The passage is Samuel Thomas’s 1865 testimony about freedpeople. The question refers to Hamilton’s Federalist No. 15, whose passage is absent.',
        'reviewed': '2026-09-30',
    } for row in (22, 44, 130)
}


def visitor_questions(subject):
    return [q for q in questions(subject) if q['id'] not in ISSUES]


def split_question(text):
    # Preserve source content; separate only the final question line for readability.
    lines = text.splitlines()
    if len(lines) < 2:
        return '', text
    return '\n'.join(lines[:-1]), lines[-1]


def session_json(state):
    return json.dumps({
        'purpose': 'Personal visitor challenge; not a full benchmark evaluation',
        'selection': 'Random ten-item selection excluding the three reviewed passage mismatches',
        'opponent': state['opponent'],
        'items': [{**{k: v for k, v in q.items() if k != 'answer' or q['id'] in state['answers']},
                   'your_answer': state['answers'].get(q['id']),
                   'model_response': state['model_answers'].get(q['id']) if q['id'] in state['answers'] else None,
                   'reflection': state.get('reflections', {}).get(q['id'])}
                  for q in state['questions']],
    }, indent=2, ensure_ascii=False)
