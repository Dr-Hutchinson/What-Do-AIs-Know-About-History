import streamlit as st

def app():

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.write(' ')

    with col2:
        st.image('./logo.png', width=600, caption="Designed with Midjourney")

    with col3:
        st.write(' ')

    with col4:
        st.write(' ')

    with col5:
        st.write(' ')

    st.header("Project Goals:")

    st.write("This digital history experiment explores the potential of these technologies for academic research and as a force for disinformation. The project uses OpenAI's [GPT-3](https://en.wikipedia.org/wiki/GPT-3) model as a case study due to its accessibility and position as the subject of robust scientific study and debate.")
    st.write("In May 2022, I presented the initial findings from this project to the [Digital History Working Group for the Consortium For History of Science, Technology, And Medicine](https://www.chstm.org/content/digital-history). I expand on these findings in an academic paper currently under peer review.")
