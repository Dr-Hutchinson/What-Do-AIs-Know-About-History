import streamlit as st

# Custom imports
from multipage import MultiPage
from pages import benchmarks_results, Baconbot_1_7_1# import your pages here
#from pages import data_upload, machine_learning, metadata, data_visualize, redundant, inference # import your pages here

# Create an instance of the app
app = MultiPage()

# Title of the main page
st.title("The GPT-3 Challenge: Can AI Accurately Interpret Historical Knowledge?")

# Add all your applications (pages) here
app.add_page("1. The GPT-3 History Challenge: Can AIs Answer Advanced Placement History Exam Questions?", benchmarks_results.app)
app.add_page("2. BaconBot: A GPT-3 Simulation of Francis Bacon [closed-access]", Baconbot_1_7_1.app)
#app.add_page("Y-Parameter Optimization",redundant.app)

# The main app
app.run()
