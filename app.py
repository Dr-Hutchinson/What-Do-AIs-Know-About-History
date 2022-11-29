import streamlit as st

# Custom imports
from multipage import MultiPage
from pages import benchmarks_results, Baconbot_1_7_1, BaconBot_1_8, primary_source_analyzer, intro, goals
#from pages import data_upload, machine_learning, metadata, data_visualize, redundant, inference # import your pages here

# Create an instance of the app
app = MultiPage()

st.set_page_config(
    page_title="What Do AIs Know About History? A Digital History Experiment by Daniel Hutchinson",
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

    st.title("What Do AIs Know About History? A Digital History Experiment")
    st.header("By Daniel Hutchinson")
    #st.subheader("Created by Daniel Hutchinson")

# Add all your applications (pages) here
app.add_page("1. Project Overview", intro.app)
app.add_page('2. What Does an AI "Know" About A.P. History?', benchmarks_results.app)
app.add_page('3. How does an AI "Interpret" a Primary Source?', primary_source_analyzer.app)
app.add_page("4. Can an AI Simulate a Historical Worldview?", BaconBot_1_8.app)
app.add_page('5. Project Goals, Methods, and Acknowledgements', goals.app)
#app.add_page("5. BaconBot: An AI Simulation of Francis Bacon (Research)", Baconbot_1_7_1.app)


#app.add_page("Y-Parameter Optimization",redundant.app)

# The main app
app.run()
