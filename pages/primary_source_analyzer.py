import os
import openai
import streamlit as st
from datetime import datetime as dt
import pandas as pd
from numpy import mean
import streamlit_authenticator as stauth
import pygsheets
from google.oauth2 import service_account
import ssl


#st.set_page_config(
    #page_title='Simulated Conversations with Francis Bacon',
    #layout='wide',
    #page_icon='🔍'
#)

def app():

    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']

    credentials = service_account.Credentials.from_service_account_info(
                    st.secrets["gcp_service_account"], scopes = scope)

    gc = pygsheets.authorize(custom_credentials=credentials)

    st.title('How does an AI "Interpret" a Primary Source?')
    st.header("Public Demo")
    col1, col2 = st.columns([3.0,3.5])

    def button_one():

        st.write("The following app prompts GPT-3 to simulate historical analysis of selected primary sources through a specific historical method.")

        def hayseed_question():
            with col1:
                with st.form('Hayseed Question'):

                    prompt = "You are an AI historian specializing in primary source analysis and historiographical interpretation. When given a Primary Source, you will provide a detailed and substantive analysis of that source based on the Historical Method and Source Information below."
                    historical_method = "Step 1 -  Contextualization: Apply the Source Information to provide a lengthy, detailed, and substantive analysis of how the Primary Source reflects the larger historical period in which it was created. In composing this lengthy, detailed, and substantive analysis, note specific events, personalities, and ideologies that shaped the the period noted in the Source Information.\nStep 2 - Purpose : Offer a substantive exploration of the purpose of the Primary Source, interpreting the author’s arguments through the Contextualization offered in Step 1.\nStep 3 - Audience: Compose a substantive assessment of the intended audience of the Primary Source. Note how this audience would shape the Primary Source's reception and historical impact in light of the Contextualization offered in Step 1.\nStep 4 - Historiographical Interpretation: Provide a substantive and incisive interpretation of how at least three specific schools of historiographical thought would interpret this source. Compare and contrast how this source could be interpreted by three different academic historiographical schools.  Different historiographical approaches could include the Progressive, Consensus, Annales, microhistory, Marxist, postmodern, post-colonial, Structuralist, gender history, and the cultural turn."
                    instructions = "Instructions: Based on the Historical Method outlined above, provide a substantive and detailed analysis of the Primary Source in the manner of an academic historian. Let's take this step by step."

                    st.header('Primary Source - "The Hayseed" (1890)')

                    hayseed_lyrics = '"The Hayseed"\n"I was once a tool of oppression\nAnd as green as a sucker could be\nAnd monopolies banded together\nTo beat a poor hayseed like me.\n"The railroads and old party bosses\nTogether did sweetly agree;\nAnd they thought there would be little trouble\nIn working a hayseed like me. . . ."'
                    source_information = "Source Information: The Primary Source is an American political campaign song popularized in 1890, and published by a Nebraska newspaper known as the Farmer's Alliance."

                    st.image(image='./hayseed.png', caption="Arthur L. Kellog, “The Hayseed,” Farmers Alliance (4 October 1890). Nebraska Newspapers (University of Nebraska Libraries), [link](https://nebnewspapers.unl.edu/lccn/2017270209/1890-10-04/ed-1/seq-1/)")
                    st.write("Arthur L. Kellog, “The Hayseed,” Farmers Alliance (4 October 1890). Nebraska Newspapers (University of Nebraska Libraries), [link](https://nebnewspapers.unl.edu/lccn/2017270209/1890-10-04/ed-1/seq-1/)")
                    st.write(source_information)

                    submit_button_1 = st.form_submit_button(label='Analyze Source')
                        #with st.expander("Test:"):
                            #test = st.radio("Test",["test1", "test2"])

                    if submit_button_1:

                        os.environ["OPENAI_API_KEY"] = st.secrets["openai_api_key"]
                        now = dt.now()

                        #model selection for OpenAI query


                        primary_source_analysis = prompt + "\n" + historical_method + "\n\n" + "Primary Source: " + "\n" + hayseed_lyrics + "\n" + source_information + "\n" + instructions + "\n"

                            #prompt_text = prompt_choice + "\n\nQ:"

                        response_length = 1500

                        openai.api_key = os.getenv("OPENAI_API_KEY")

                        summon = openai.Completion.create(
                            model="text-davinci-002",
                            prompt=primary_source_analysis,
                            temperature=0,
                            user="0",
                            max_tokens=response_length,
                            frequency_penalty=0.35,
                            presence_penalty=0.25)

                        response_json = len(summon["choices"])

                        for item in range(response_json):
                            output = summon['choices'][item]['text']

                        response = openai.Completion.create(
                                engine="content-filter-alpha",
                                prompt= "<|endoftext|>"+output+"\n--\nLabel:",
                                temperature=0,
                                max_tokens=1,
                                user="0",
                                top_p=0,
                                logprobs=10)

                        output_label = response["choices"][0]["text"]

                            # OpenAI Content Filter code - comments in this section from OpenAI documentation: https://beta.openai.com/docs/engines/content-filter
                                # This is the probability at which we evaluate that a "2" is likely real
                                    # vs. should be discarded as a false positive

                        def filter_function():
                            output_label = response["choices"][0]["text"]
                            toxic_threshold = -0.355

                            if output_label == "2":
                                    # If the model returns "2", return its confidence in 2 or other output-labels
                                logprobs = response["choices"][0]["logprobs"]["top_logprobs"][0]

                                    # If the model is not sufficiently confident in "2",
                                    # choose the most probable of "0" or "1"
                                    # Guaranteed to have a confidence for 2 since this was the selected token.
                                if logprobs["2"] < toxic_threshold:
                                    logprob_0 = logprobs.get("0", None)
                                    logprob_1 = logprobs.get("1", None)

                                        # If both "0" and "1" have probabilities, set the output label
                                        # to whichever is most probable
                                    if logprob_0 is not None and logprob_1 is not None:
                                        if logprob_0 >= logprob_1:
                                            output_label = "0"
                                        else:
                                            output_label = "1"
                                        # If only one of them is found, set output label to that one
                                    elif logprob_0 is not None:
                                        output_label = "0"
                                    elif logprob_1 is not None:
                                        output_label = "1"

                                        # If neither "0" or "1" are available, stick with "2"
                                        # by leaving output_label unchanged.

                                # if the most probable token is none of "0", "1", or "2"
                                # this should be set as unsafe
                            if output_label not in ["0", "1", "2"]:
                                output_label = "2"

                            return output_label

                                # filter or display OpenAI outputs, record outputs to Google Sheets API
                        if int(filter_function()) < 2:
                            st.write("GPT's Analysis:")
                            st.write(output)
                            #st.write("\n\n\n\n")
                            #st.subheader('As Lord Bacon says, "Truth will sooner come out from error than from confusion."  Please click on the Rank Bacon button above to rank this reply for future improvement.')
                        elif int(filter_function()) == 2:
                            st.write("The OpenAI content filter ranks Bacon's response as potentially offensive. Per OpenAI's use policies, potentially offensive responses will not be displayed.")

                        st.write("\n\n\n\n")
                        st.write("OpenAI's Content Filter Ranking: " +  output_label)


                        #def total_output_collection():
                            #d1 = {'user':["0"], 'user_id':["0"], 'model':[model_choice], 'prompt':[prompt_choice_freeform], 'prompt_boost':[prompt_boost_question_1 + "\n\n" + prompt_boost_question_2], 'question':[question], 'output':[output], 'temperature':[temperature_dial], 'response_length':[response_length], 'filter_ranking':[output_label], 'date':[now]}
                            #df1 = pd.DataFrame(data=d1, index=None)
                            #sh1 = gc.open('bacon_outputs')
                            #wks1 = sh1[0]
                            #cells1 = wks1.get_all_values(include_tailing_empty_rows=False, include_tailing_empty=False, returnas='matrix')
                            #end_row1 = len(cells1)
                            #wks1.set_dataframe(df1,(end_row1+1,1), copy_head=False, extend=True)

                        #def output_collection_filtered():
                            #d2 = {'user':["0"], 'user_id':["0"], 'model':[model_choice], 'prompt':[prompt_choice_freeform], 'prompt_boost':[prompt_boost_question_1 + "\n\n" + prompt_boost_question_2], 'question':[question], 'output':[output], 'temperature':[temperature_dial], 'response_length':[response_length], 'filter_ranking':[output_label], 'date':[now]}
                            #df2 = pd.DataFrame(data=d2, index=None)
                            #sh2 = gc.open('bacon_outputs_filtered')
                            #wks2 = sh2[0]
                            #cells2 = wks2.get_all_values(include_tailing_empty_rows=False, include_tailing_empty=False, returnas='matrix')
                            #end_row2 = len(cells2)
                            #wks2.set_dataframe(df2,(end_row2+1,1), copy_head=False, extend=True)

                        #def temp_output_collection():
                            #d3 = {'user':["0"], 'user_id':["0"], 'model':[model_choice], 'prompt':[prompt_choice_freeform], 'prompt_boost':[prompt_boost_question_1 + "\n\n" + prompt_boost_question_2], 'question':[question], 'output':[output], 'temperature':[temperature_dial], 'response_length':[response_length], 'filter_ranking':[output_label], 'date':[now]}
                            #df3 = pd.DataFrame(data=d3, index=None)
                            #sh3 = gc.open('bacon_outputs_temp')
                            #wks3 = sh3[0]
                            #wks3.set_dataframe(df3,(1,1))

                        #if int(filter_function()) == 2:
                            #output_collection_filtered()
                            #total_output_collection()
                        #else:
                            #temp_output_collection()
                            #total_output_collection()

        with st.sidebar.form(key ='Form2'):
            field_choice = st.radio("Choose a Primary Source:", ['"The Hayseed" (U.S. History)'])

            button2 = st.form_submit_button("Click here to load the Primary Source.")

            if field_choice == '"The Hayseed" (U.S. History)':
                field_choice = hayseed_question()
            #elif field_choice == "Philosophy of Science":
                #field_choice = philosophy_questions()

        #with st.sidebar:
            #st.write('Explore more about the life and times of Francis Bacon:')
            #st.write('[Six Degrees of Francis Bacon](http://www.sixdegreesoffrancisbacon.com/), Carnegie Mellon University')
            #st.write('[Jürgen Klein and Guido Giglioni, "Francis Bacon", The Stanford Encyclopedia of Philosophy](https://plato.stanford.edu/entries/francis-bacon/)')
            #st.write('[Richard S. Westfall, "Francis Bacon", The Galileo Project, Rice University](http://galileo.rice.edu/Catalog/NewFiles/bacon.html)')


        #pygsheets credentials for Google Sheets API


        #with col2:
            #bacon_pic = st.image(image='./bacon.png', caption="Portrait of Francis Bacon. National Portrait Gallery, London.")

    def button_two():
        #Rank Bacon_bot Responses

        with col1:
            st.write("Rank GPT-3's Interpretations:")
            sh1 = gc.open('bacon_outputs_temp')

            wks1 = sh1[0]
            submission_text = wks1.get_value('F2')
            output = wks1.get_value('G2')
            prompt_text = wks1.get_value('D2')
            st.subheader('Prompt:')
            st.write(prompt_text)
            st.subheader('Your Question')
            st.write(submission_text)
            st.subheader("Bacon's Reply:")
            st.write(output)

            with st.form('form2'):
                bacon_score = st.slider("How much does the reply resemble the style of Francis Bacon?", 0, 10, key='bacon')
                worldview_score = st.slider("Is the reply consistent with Bacon's worldview?", 0, 10, key='worldview')
                accuracy_rank = st.slider("Does the reply appear factually accurate?", 0, 10, key='accuracy')
                coherence_rank = st.slider("How coherent and well-written is the reply?", 0,10, key='coherence')
                st.write("Transmitting the rankings takes a few moments. Thank you for your patience.")
                submit_button_2 = st.form_submit_button(label='Submit Ranking')

                if submit_button_2:
                    sh1 = gc.open('bacon_outputs_temp')
                    wks1 = sh1[0]
                    df = wks1.get_as_df(has_header=True, index_column=None, start='A1', end=('K2'), numerize=False)
                    name = df['user'][0]
                    user_id = df['user_id'][0]
                    model_choice = df['model'][0]
                    prompt_choice = df['prompt'][0]
                    prompt_boost = df['prompt_boost'][0]
                    submission_text = df['question'][0]
                    output = df['output'][0]
                    temperature_dial = df['temperature'][0]
                    response_length = df['response_length'][0]
                    output_label = df['filter_ranking'][0]
                    now = dt.now()
                    ranking_score = [bacon_score, worldview_score, accuracy_rank, coherence_rank]
                    ranking_average = mean(ranking_score)

                    def ranking_collection():
                        d4 = {'user':["0"], 'user_id':[user_id],'model':[model_choice], 'prompt':[prompt_choice], 'prompt_boost':[prompt_boost],'question':[submission_text], 'output':[output], 'temperature':[temperature_dial], 'response_length':[response_length], 'filter_ranking':[output_label], 'bacon_score':[bacon_score], 'worldview_score':[worldview_score],'accuracy_rank':[accuracy_rank], 'coherence':[coherence_rank], 'overall_ranking':[ranking_average], 'date':[now]}
                        df4 = pd.DataFrame(data=d4, index=None)
                        sh4 = gc.open('bacon_rankings')
                        wks4 = sh4[0]
                        cells4 = wks4.get_all_values(include_tailing_empty_rows=False, include_tailing_empty=False, returnas='matrix')
                        end_row4 = len(cells4)
                        wks4.set_dataframe(df4,(end_row4+1,1), copy_head=False, extend=True)

                    ranking_collection()
                    st.write('Rankings recorded - thank you! Feel free to continue your conversation with Francis Bacon.')

        with col2:
            bacon_pic = st.image(image='./bacon.png', caption="Portrait of Francis Bacon. National Portrait Gallery, London.")

        with st.sidebar:
            st.write('Explore more about the life and times of Francis Bacon:')
            st.write('[Six Degrees of Francis Bacon](http://www.sixdegreesoffrancisbacon.com/), Carnegie Mellon University')
            st.write('[Jürgen Klein and Guido Giglioni, "Francis Bacon", The Stanford Encyclopedia of Philosophy](https://plato.stanford.edu/entries/francis-bacon/)')
            st.write('[Richard S. Westfall, "Francis Bacon", The Galileo Project, Rice University](http://galileo.rice.edu/Catalog/NewFiles/bacon.html)')

    with col1:

        st.write("Select the 'Analyze Sources' button to explore how GPT-3 simulates historical analysis. Select 'Rank Responses' to note your impressions of these interpretations.")


        pages = {
            0 : button_one,
            1 : button_two,
        }

        if "current" not in st.session_state:

            st.session_state.current = None

        if st.button("Analyze Sources"):
            st.session_state.current = 0
        if st.button("Rank Responses"):
            st.session_state.current = 1

        if st.session_state.current != None:
            pages[st.session_state.current]()
