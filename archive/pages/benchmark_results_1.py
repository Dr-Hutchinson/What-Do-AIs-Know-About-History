# pages/benchmark_results_1.py
# -*- coding: utf-8 -*-

import re
import streamlit as st
import pandas as pd
import pygsheets
from google.oauth2 import service_account
from openai import OpenAI

APP_TITLE = 'What Does an AI "Know" About History? (Minimal Demo)'

# ---------- Resource helpers ----------

@st.cache_resource
def get_gsheets_client():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scope
    )
    return pygsheets.authorize(custom_credentials=credentials)

@st.cache_resource
def get_openai_client():
    return OpenAI(api_key=st.secrets["openai_api_key"])

def load_frames(gc: pygsheets.client.Client):
    euro = gc.open("high_school_european_history_test").sheet1
    us = gc.open("high_school_us_history_test").sheet1
    world = gc.open("high_school_world_history_test").sheet1

    # read as raw (no headers), matching your original layout
    df_euro = euro.get_as_df(has_header=False, include_tailing_empty=False)
    df_us = us.get_as_df(has_header=False, include_tailing_empty=False)
    df_world = world.get_as_df(has_header=False, include_tailing_empty=False)
    return df_euro, df_us, df_world

def pick_random_row(df: pd.DataFrame) -> pd.Series:
    clean = df.dropna(how="all")
    return clean.sample(1).iloc[0]

def parse_row(row: pd.Series):
    """
    Expected columns:
      0 question, 1 A, 2 B, 3 C, 4 D, 5 AnswerLetter(A/B/C/D)
    """
    q = str(row.iloc[0]).strip()
    A = str(row.iloc[1]).strip()
    B = str(row.iloc[2]).strip()
    C = str(row.iloc[3]).strip()
    D = str(row.iloc[4]).strip()
    ans_letter = str(row.iloc[5]).strip().upper() if len(row) > 5 else ""
    # Normalize weird entries like "A:" or "A) ..." to just "A"
    if ans_letter and ans_letter[0] in "ABCD":
        ans_letter = ans_letter[0]
    return q, A, B, C, D, ans_letter

def mcq_prompt_plain(question: str, A: str, B: str, C: str, D: str) -> str:
    # A simple, readable prompt; no JSON/format constraints
    return (
        "Answer the following multiple-choice question. "
        "Analyze briefly, then state your final choice (A/B/C/D) on a new line starting with 'Answer: '.\n\n"
        f"Question:\n{question}\n\n"
        f"Options:\nA. {A}\nB. {B}\nC. {C}\nD. {D}\n"
    )

def letter_to_text(letter: str, A: str, B: str, C: str, D: str) -> str:
    mapping = {"A": A, "B": B, "C": C, "D": D}
    return mapping.get(letter.upper(), "")

# --- NEW: simple parser for the model's final choice ---
def extract_model_letter(raw_reply: str) -> str:
    """
    Try a few forgiving patterns to pull A/B/C/D from the raw model output.
    Priority:
      1) line like "Answer: C"
      2) "Final answer: B"
      3) standalone A/B/C/D token at line end or before punctuation
    Returns "" if not found.
    """
    text = raw_reply.strip()

    # 1) Preferred form: "Answer: X"
    m = re.search(r'(?i)\banswer\s*:\s*([ABCD])\b', text)
    if m:
        return m.group(1).upper()

    # 2) Common variant
    m = re.search(r'(?i)\bfinal\s*answer\s*:\s*([ABCD])\b', text)
    if m:
        return m.group(1).upper()

    # 3) Fallback: look for a single capital letter A-D at end of a line or before punctuation
    # (avoid matching letters inside words)
    m = re.search(r'(?m)(?:^|\s)([ABCD])(?=[\s\).:;,-]*$)', text)
    if m:
        return m.group(1).upper()

    return ""

# ---------- PAGE ENTRY POINT ----------

def app():
    st.header(APP_TITLE)
    st.caption("Minimal demo: loads a random AP question and shows the **raw** model reply. Now also displays the official answer and a simple Correct/Incorrect check.")

    # Sidebar controls
    with st.sidebar:
        subject = st.radio("Subject", ["U.S. History", "European History", "World History"], index=0)
        model = st.selectbox(
            "Model",
            ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini"],  # adjust as you like
            index=0,
        )
        reload_q = st.button("Load another random question")

    if reload_q:
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.experimental_rerun()

    # Data sources
    gc = get_gsheets_client()
    df_euro, df_us, df_world = load_frames(gc)

    # Pick source dataframe
    df = df_us if subject == "U.S. History" else (df_euro if subject == "European History" else df_world)

    # Sample 1 random question
    row = pick_random_row(df)
    q, A, B, C, D, ans_letter = parse_row(row)

    # Persist to session so the MCQ stays stable for this view
    ss = st.session_state
    ss.setdefault("subject", subject)
    ss.setdefault("question_text", q)
    ss.setdefault("A", A)
    ss.setdefault("B", B)
    ss.setdefault("C", C)
    ss.setdefault("D", D)
    ss.setdefault("ans_letter", ans_letter)  # we use this for display/check

    # Layout
    col1, col2 = st.columns(2)

    # ----- Human side -----
    with col1:
        st.subheader("Human")
        st.write("**Question**")
        st.write(ss["question_text"])
        choice = st.radio(
            "Your choice:",
            [f"A: {ss['A']}", f"B: {ss['B']}", f"C: {ss['C']}", f"D: {ss['D']}"],
            index=0,
            key="human_choice",
        )

    # ----- Model side -----
    with col2:
        st.subheader("Model")
        st.caption("Plain Chat Completions call; raw content shown below.")
        if st.button("Ask the Model"):
            client = get_openai_client()
            prompt = mcq_prompt_plain(ss["question_text"], ss["A"], ss["B"], ss["C"], ss["D"])

            try:
                resp = client.chat.completions.create(
                    model=model,
                    temperature=0,
                    messages=[
                        {"role": "system", "content": "You are a careful historian and test-taker."},
                        {"role": "user", "content": prompt},
                    ],
                )
                content = resp.choices[0].message.content if resp.choices else "(no content)"
                st.markdown("**Raw model reply:**")
                st.code(content)

                # ---- Show official answer from the sheet ----
                correct_letter = ss["ans_letter"]
                if correct_letter in ("A", "B", "C", "D"):
                    correct_text = letter_to_text(correct_letter, ss["A"], ss["B"], ss["C"], ss["D"])
                    st.markdown("**Official answer (from sheet):**")
                    st.info(f"{correct_letter}: {correct_text}")
                else:
                    st.warning("No official answer letter found in the sheet for this question.")

                # ---- Try to extract the model's final letter and show verdict ----
                model_letter = extract_model_letter(content)
                if model_letter:
                    if correct_letter in ("A", "B", "C", "D"):
                        if model_letter == correct_letter:
                            st.success(f"Model marked as **Correct** (Model: {model_letter})")
                        else:
                            st.error(f"Model marked as **Incorrect** (Model: {model_letter}, Correct: {correct_letter})")
                    else:
                        st.caption(f"Model chose: {model_letter} (not scored; no official answer available)")
                else:
                    st.caption("Couldn’t detect a final letter (A/B/C/D) in the model’s reply.")

                # Optional: token usage if available
                usage = getattr(resp, "usage", None)
                if usage:
                    st.caption(f"Tokens — prompt: {getattr(usage, 'prompt_tokens', 'n/a')}, "
                               f"completion: {getattr(usage, 'completion_tokens', 'n/a')}, "
                               f"total: {getattr(usage, 'total_tokens', 'n/a')}")

            except Exception as e:
                st.error(f"Model call failed: {e}")
