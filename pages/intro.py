import streamlit as st

def app():

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.write(' ')

    with col2:
        st.image('./output_project_aperture_crop.png', width=600, caption="Designed with DALL-E")

    with col3:
        st.write(' ')

    with col4:
        st.write(' ')

    with col5:
        st.write(' ')

    #st.title("Can AIs Accurately Interpret History? A Digital History Experiment")

    st.header("Project Description")

    st.write("This digital history experiment examines the following question: can AIs accurately interpret the past?  Recent advances in machine learning have resulted in new computational models capable of remarkable imitation of human analytical capabilities. Among the most studied of these models is [GPT-3](https://en.wikipedia.org/wiki/GPT-3) (Generative Pre-trained Transformer-3). In this project, users can pose historical questions to GPT-3 and observe its responses. This project enables historians and the public to directly probe the historical capacities of advanced AIs, and gauge for themselves the possibilities and perils of this technology. With such knowledge, we can better assess AI’s potential impact on understanding of the past, and consider the broader implications of this technology for the future.")

    st.header("Project Elements")

    st.write("**What Does an AI “Know” about History?**: In this section, humans can test their historical knowledge against that of an AI. Users can answer multiple choice questions from the Advanced Placement (A.P.) curriculums for U.S., European, and World history, and then compare their performance against GPT-3. Accompanying these questions is data on GPT-3's overall performance on these questions.")

    st.write("**How Does an AI “Interpret” a Primary Source?**: Here users can prompt GPT-3 to analyze and interpret a selection of primary sources. GPT-3 will attempt to offer the source’s context, purpose, intended audience, and possible historiographical interpretations of the source.")

    st.write("**Can an AI Simulate a Historical Worldview?**: In this section users can pose questions to an AI instructed to imitate a figure from history: [Francis Bacon](https://en.wikipedia.org/wiki/Francis_Bacon) (1561-1626), former Lord Chancellor of England under Queen Elizabeth I and King James I, and a key figure in the Scientific Revolution.")

    st.write("**Implications and Ethical Considerations:** This section offers initial thoughts on the potential implications and ethical challenges of these technologies.")

    st.write("**Credits & Technical Details**: Additional detail is provided on the methods used in this project, and acknowledgements of those who helped make this project possible.")
