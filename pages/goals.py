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

    st.header("Project Methods:")

    st.write("The project employs [Streamlit](https://streamlit.io/) to run Python scripts calling OpenAI's API for GPT-3. GPT-3's outputs are products of specialized prompts informed by current research in prompt engineering. Specific methods include [few shot prompting](https://arxiv.org/abs/2005.14165) and [chain-of-thought reasoning](https://arxiv.org/abs/2210.03493). The project's [GitHub repository](https://github.com/Dr-Hutchinson/gpt-3_challenge) contains the full text of these prompts.")

    st.header("Acknowledgements:")

    st.write("Many thanks to Abraham Gibson for the invitation to the CHSTM's Digital History Working Group share this research, and to my colleagues William Mattingly, Patrick Wadden, and Ian Crowe for their thoughtful feedback.")
    st.write("This project was supported by a sabbatical semester awarded by the Office of Academic Affairs at Belmont Abbey College. My thanks to Provost Travis Feezell and Vice Provost David Williams for their support of this effort.")
