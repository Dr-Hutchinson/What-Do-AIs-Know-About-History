# streamlit run app.py
# -*- coding: utf-8 -*-

import os
import json
import time
from datetime import datetime as dt

import pandas as pd
import streamlit as st
from openai import OpenAI
import pygsheets
from google.oauth2 import service_account


# ============ Config / Constants ============

APP_TITLE = "What Does an AI 'Know' About History?"
MODEL_DEFAULTS = ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini"]  # adjust as needed
MAX_RETRIES = 3
BACKOFF_BASE_SEC = 0.8


# ============ Utilities ============

@st.cache_resource
def get_gsheets_client():
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scope
    )
    return pygsheets.authorize(custom_credentials=credentials)

@st.cache_resource
def get_openai_client():
    return OpenAI(api_key=st.secrets["openai_api_key"])

def load_question_frames(gc: pygsheets.client.Client):
    """Load your three AP history sheets and the benchmark sheet."""
    euro_sheet = gc.open('high_school_european_history_test').sheet1
    us_sheet = gc.open('high_school_us_history_test').sheet1
    world_sheet = gc.open('high_school_world_history_test').sheet1
    benchmarks_sheet = gc.open('benchmark_tests').sheet1

    # Your original code treated the first row as data (no headers),
    # so we read without headers to keep your index/iloc logic stable.
    df_euro = euro_sheet.get_as_df(has_header=False, index_col=None, include_tailing_empty=False)
    df_us = us_sheet.get_as_df(has_header=False, index_col=None, include_tailing_empty=False)
    df_world = world_sheet.get_as_df(has_header=False, index_col=None, include_tailing_empty=False)

    # Benchmarks sheet: first row is headers in your original code
    df4_preheaders = benchmarks_sheet.get_as_df(has_header=False, index_col=None, include_tailing_empty=False)
    df_benchmarks = df4_preheaders.rename(columns=df4_preheaders.iloc[0]).drop(df4_preheaders.index[0])

    return df_euro, df_us, df_world, df_benchmarks, benchmarks_sheet

def pick_random_row(df: pd.DataFrame) -> pd.DataFrame:
    """Return a single-row dataframe sample."""
    # Safety: drop fully empty rows if any
    clean = df.dropna(how="all")
    return clean.sample(1, random_state=None)

def question_tuple_from_row(row: pd.Series):
    """
    Expecting columns:
    0: question, 1: A, 2: B, 3: C, 4: D, 5: Answer Letter (A/B/C/D)
    """
    q = str(row.iloc[0]).strip()
    A = str(row.iloc[1]).strip()
    B = str(row.iloc[2]).strip()
    C = str(row.iloc[3]).strip()
    D = str(row.iloc[4]).strip()
    ans_letter = str(row.iloc[5]).strip().upper()
    if ans_letter not in {"A", "B", "C", "D"}:
        # Fallback: try to detect leading letter in the answer cell
        head = ans_letter[:1]
        ans_letter = head if head in {"A", "B", "C", "D"} else "A"
    return q, A, B, C, D, ans_letter

def letter_to_text(letter: str, A: str, B: str, C: str, D: str) -> str:
    return {"A": A, "B": B, "C": C, "D": D}[letter.upper()]

def parse_human_choice_label(radio_value: str) -> str:
    """
    Radio values look like "A: <text>".
    Extract the first char as the chosen letter.
    """
    return radio_value[:1].upper()

def write_benchmark_row(benchmarks_sheet, field, qnum, correct_letter, correct_text,
                        model_letter, model_text, status):
    now = dt.now()
    # Get current used range to find next row
    cells = benchmarks_sheet.get_all_values(
        include_tailing_empty_rows=False,
        include_tailing_empty=False,
        returnas='matrix'
    )
    end_row = len(cells)

    # Keep your original column names
    d = {
        'field': [field],
        'question_number': [qnum],
        'correct_answer': [f"{correct_letter}: {correct_text}"],
        'output_answer': [f"{model_letter}: {model_text}"],
        'correct_status': [status],
        'time': [now]
    }
    dfw = pd.DataFrame(d)
    benchmarks_sheet.set_dataframe(dfw, (end_row + 1, 1), copy_head=False, extend=True)

def make_mcq_prompt(question_text: str, A: str, B: str, C: str, D: str) -> str:
    return f"""You are evaluating a multiple-choice question.
Return ONLY valid JSON that matches the provided schema.

Question:
{question_text}

Options:
A. {A}
B. {B}
C. {C}
D. {D}

Instructions:
- Select the single best answer (A, B, C, or D).
- Set "answer" to the letter only (A|B|C|D).
- Set "choice_text" to the exact text of that option.
- Provide a brief "rationale".
"""

def model_schema(strict: bool = True) -> dict:
    """
    JSON schema for structured outputs.
    We set additionalProperties=false to keep outputs clean.
    """
    return {
        "name": "mcq_answer",
        "strict": strict,
        "schema": {
            "type": "object",
            "properties": {
                "answer": {
                    "type": "string",
                    "description": "One of A, B, C, or D (just the letter).",
                    "enum": ["A", "B", "C", "D"]
                },
                "choice_text": {
                    "type": "string",
                    "description": "Verbatim text of the chosen option."
                },
                "rationale": {
                    "type": "string",
                    "description": "A brief 1-3 sentence justification."
                }
            },
            "required": ["answer", "choice_text"],
            "additionalProperties": False
        }
    }

def ask_model_mcq(client: OpenAI, model: str, question_text: str, A: str, B: str, C: str, D: str) -> dict:
    """
    Calls the Responses API with structured JSON output.
    Returns dict: {"answer": "A", "choice_text": "...", "rationale": "..."}
    Has a safe fallback to JSON-mode if schema is unsupported.
    """
    prompt = make_mcq_prompt(question_text, A, B, C, D)
    schema = model_schema(strict=True)

    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            # Primary: structured outputs via json_schema
            resp = client.responses.create(
                model=model,
                input=prompt,
                temperature=0,
                max_output_tokens=150,
                response_format={"type": "json_schema", "json_schema": schema},
            )
            text = resp.output_text
            data = json.loads(text)
            # Minimal validation
            ans = str(data.get("answer", "")).strip().upper()
            if ans not in {"A", "B", "C", "D"}:
                raise ValueError(f"Invalid answer letter in structured output: {ans}")
            return {
                "answer": ans,
                "choice_text": str(data.get("choice_text", "")).strip(),
                "rationale": str(data.get("rationale", "")).strip()
            }

        except Exception as e:
            last_err = e
            # Fallback path: try JSON mode (no schema enforcement)
            try:
                resp = client.responses.create(
                    model=model,
                    input=prompt + "\nReturn ONLY JSON in the shape {\"answer\":\"A|B|C|D\",\"choice_text\":\"...\",\"rationale\":\"...\"}.",
                    temperature=0,
                    max_output_tokens=150,
                    response_format={"type": "json_object"},
                )
                text = resp.output_text
                data = json.loads(text)
                ans = str(data.get("answer", "")).strip().upper()
                if ans not in {"A", "B", "C", "D"}:
                    raise ValueError(f"Invalid answer in JSON fallback: {ans}")
                return {
                    "answer": ans,
                    "choice_text": str(data.get("choice_text", "")).strip(),
                    "rationale": str(data.get("rationale", "")).strip()
                }
            except Exception as e2:
                last_err = e2
                time.sleep(BACKOFF_BASE_SEC * (attempt + 1))

    raise RuntimeError(f"Model call failed after retries: {last_err!r}")


# ============ Streamlit App ============

def app():
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    st.header(APP_TITLE)

    st.subheader("Instructions")
    st.write(
        "This app lets you test your historical knowledge against current OpenAI models. "
        "Choose an A.P. category, answer a random question, then compare with the model."
    )

    st.subheader("Background")
    st.write(
        "Earlier assessments (e.g., Hendrycks et al., 2021/2022) benchmarked model performance on "
        "history questions. This app updates your original workflow with modern API calls and structured outputs."
    )

    # Sidebar controls
    with st.sidebar:
        st.markdown("### Configure")
        field_choice = st.radio("Subject", ["U.S. History", "European History", "World History"], index=0)
        model_choice = st.selectbox("Model", MODEL_DEFAULTS, index=0)
        reload = st.button("Load another random question")

    # Reset session if user clicks reload
    if reload:
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.experimental_rerun()

    # Clients
    gc = get_gsheets_client()
    client = get_openai_client()

    # Load data
    df_euro, df_us, df_world, df_bench_df, benchmarks_sheet = load_question_frames(gc)

    # Choose field df and sample 1 row
    if field_choice == "U.S. History":
        field_df = df_us
    elif field_choice == "European History":
        field_df = df_euro
    else:
        field_df = df_world

    sampled = pick_random_row(field_df)
    # Capture the original sheet index as "question_number"
    question_number = str(sampled.index[0])

    q, A, B, C, D, ans_letter = question_tuple_from_row(sampled.iloc[0])
    correct_text = letter_to_text(ans_letter, A, B, C, D)

    # Persist into session_state to keep stable across forms
    ss = st.session_state
    ss.setdefault("field", field_choice)
    ss.setdefault("question_number", question_number)
    ss.setdefault("question", q)
    ss.setdefault("A", A)
    ss.setdefault("B", B)
    ss.setdefault("C", C)
    ss.setdefault("D", D)
    ss.setdefault("answer_letter", ans_letter)
    ss.setdefault("answer_text", correct_text)

    col1, col2 = st.columns(2)

    # ---------- Human Interface ----------
    with col1:
        st.subheader("Human Interface")
        st.write(f"**Question #{ss['question_number']}**")
        st.write(ss["question"])

        human_choice = st.radio(
            "Choose one:",
            [f"A: {ss['A']}", f"B: {ss['B']}", f"C: {ss['C']}", f"D: {ss['D']}"],
            index=0,
            key="human_radio"
        )
        if st.button("Submit Your Answer"):
            chosen_letter = parse_human_choice_label(human_choice)
            is_correct = (chosen_letter == ss["answer_letter"])
            st.success("Correct!") if is_correct else st.error("Incorrect.")
            st.info(f"Answer — {ss['answer_letter']}: {ss['answer_text']}")

    # ---------- Model Interface ----------
    with col2:
        st.subheader("Model Interface")
        st.caption("Uses the OpenAI Responses API with structured JSON output.")
        if st.button("Ask the Model"):
            try:
                result = ask_model_mcq(
                    client=client,
                    model=model_choice,
                    question_text=ss["question"],
                    A=ss["A"], B=ss["B"], C=ss["C"], D=ss["D"]
                )
                model_letter = result["answer"]
                model_text = result["choice_text"]
                rationale = result.get("rationale", "")

                is_correct = (model_letter == ss["answer_letter"])
                st.write(f"**Model’s Answer:** {model_letter}")
                st.write(model_text)
                if rationale:
                    st.caption(rationale)
                st.success("Model: Correct") if is_correct else st.error("Model: Incorrect")

                # Persist (for continuity with your prior sheet shape)
                ss["model_output_display"] = f"{model_letter}: {model_text}"

                # Log to benchmarks sheet
                write_benchmark_row(
                    benchmarks_sheet,
                    field=ss["field"],
                    qnum=ss["question_number"],
                    correct_letter=ss["answer_letter"],
                    correct_text=ss["answer_text"],
                    model_letter=model_letter,
                    model_text=model_text,
                    status=("correct" if is_correct else "incorrect")
                )

            except Exception as e:
                st.error(f"Model call failed: {e}")

    # ---------- Quick accuracy snapshot ----------
    st.markdown("---")
    st.subheader("Quick Snapshot")
    st.write(
        "Below is the overall correctness distribution in your `benchmark_tests` sheet. "
        "This is a quick look across **all** fields logged so far."
    )
    try:
        # Re-read to include the row just written
        df4_preheaders = benchmarks_sheet.get_as_df(has_header=False, index_col=None, include_tailing_empty=False)
        df_bench = df4_preheaders.rename(columns=df4_preheaders.iloc[0]).drop(df4_preheaders.index[0])
        if "correct_status" in df_bench.columns:
            st.bar_chart(df_bench["correct_status"].value_counts())
        else:
            st.info("No 'correct_status' column found yet in benchmark sheet.")
    except Exception as e:
        st.warning(f"Could not load benchmark snapshot: {e}")

