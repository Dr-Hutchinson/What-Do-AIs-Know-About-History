import streamlit as st

# Custom imports
from multipage import MultiPage
from pages import benchmarks_results, Baconbot_1_7_1
#from pages import data_upload, machine_learning, metadata, data_visualize, redundant, inference # import your pages here

# Create an instance of the app
app = MultiPage()

st.set_page_config(
    page_title="The GPT-3 Challenge: Can AI's Accurately Interpret Historical Knowledge?",
    layout='wide',
    page_icon='🔍'
)
# Title of the main page
with st.sidebar:
    st.title("The GPT-3 Challenge: Can AI's Accurately Interpret Historical Knowledge?")

# Add all your applications (pages) here
app.add_page("1. What Do AIs Know about History?", benchmarks_results.app)
app.add_page("2. BaconBot [closed-access]", Baconbot_1_7_1.app)
#app.add_page("Y-Parameter Optimization",redundant.app)

# The main app
app.run()
