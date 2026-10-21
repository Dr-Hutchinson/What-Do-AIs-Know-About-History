import streamlit as st

from views import about, quiz, results, critique

st.set_page_config(page_title="What Do AIs Know About History?", page_icon="📚", layout="wide")
st.markdown("""<style>
.block-container {max-width:1120px;padding-top:2.4rem;}
[data-testid="stRadio"] label {padding:.55rem .7rem;border-radius:8px;}
[data-testid="stRadio"] label:hover {background:rgba(18,124,112,.09);}
[data-testid="stText"] {white-space:pre-wrap;line-height:1.7;font-size:1rem;font-family:inherit;}
</style>""", unsafe_allow_html=True)
st.sidebar.title("What Do AIs Know About History?")
st.sidebar.caption("Take the challenge. Inspect the answers. Question the score.")
pages = {
    'about': st.Page(about, title="Start here", default=True),
    'quiz': st.Page(quiz, title="You versus the model", url_path="quiz"),
    'critique': st.Page(critique, title="Question the benchmark", url_path="critique"),
    'results': st.Page(results, title="Explore model performance", url_path="results"),
}
st.session_state.navigation_pages = pages
page = st.navigation(list(pages.values()))
page.run()
