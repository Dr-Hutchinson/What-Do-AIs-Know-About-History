"""Visitor curation and downloadable session records; canonical data stays unchanged."""
import json
from pathlib import Path
from history import questions

AUDIT_PATH = Path(__file__).resolve().parent / 'data/STRUCTURAL_AUDIT_2026-10-21.json'
ISSUES = json.loads(AUDIT_PATH.read_text(encoding='utf-8'))['issues']


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
        'selection': f'Random ten-item selection excluding {len(ISSUES)} reviewed structurally defective items across all subjects',
        'opponent': state['opponent'],
        'items': [{**{k: v for k, v in q.items() if k != 'answer' or q['id'] in state['answers']},
                   'your_answer': state['answers'].get(q['id']),
                   'model_response': state['model_answers'].get(q['id']) if q['id'] in state['answers'] else None,
                   'reflection': state.get('reflections', {}).get(q['id'])}
                  for q in state['questions']],
    }, indent=2, ensure_ascii=False)
