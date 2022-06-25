import streamlit as st

# Custom imports
from multipage import MultiPage
from pages import benchmarks_results, Baconbot_1_7_1
#from pages import data_upload, machine_learning, metadata, data_visualize, redundant, inference # import your pages here

# Create an instance of the app
app = MultiPage()

st.set_page_config(
    page_title="Can AI's Accurately Interpret History? A Digital History Experiment",
    layout='wide',
    page_icon='🔍'
)
# Title of the main page
with st.sidebar:
    st.markdown(
    """
    <style>
    [data-testid="stSidebar"][aria-expanded="true"] > div:first-child {
        width: 450px;
    }
    [data-testid="stSidebar"][aria-expanded="false"] > div:first-child {
        width: 500px;
        margin-left: -500px;
    }
    </style>
    """,
    unsafe_allow_html=True,
    )

    st.title("Can AIs Accurately Interpret History? A Digital History Experiment")
    st.subheader("Created by Daniel Hutchinson")

# Add all your applications (pages) here
app.add_page('1. What Does an AI "Know" About History?', benchmarks_results.app)
app.add_page("2. BaconBot: An AI Simulation of Francis Bacon (Limited)", Baconbot_1_7_1.app)
#app.add_page("Y-Parameter Optimization",redundant.app)

# The main app
app.run()
