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

    st.title('Can an AI "Interpret" a Primary Source?')
    st.header("Public Demo")
    col1, col2 = st.columns([5.5,.5])

    def button_one():

        st.write("The following app prompts GPT-3 to simulate historical analysis of selected primary sources through a specific historical method.")

        def hayseed_question():
            with col1:
                with st.form('Hayseed Question'):

                    question = "Hayseed"
                    prompt = "You are an AI historian specializing in primary source analysis and historiographical interpretation. When given a Primary Source, you will provide a detailed and substantive analysis of that source based on the Historical Method and Source Information below."
                    historical_method = "Step 1 -  Contextualization: Apply the Source Information to provide a lengthy, detailed, and substantive analysis of how the Primary Source reflects the larger historical period in which it was created. In composing this lengthy, detailed, and substantive analysis, note specific events, personalities, and ideologies that shaped the the period noted in the Source Information.\nStep 2 - Purpose : Offer a substantive exploration of the purpose of the Primary Source, interpreting the author’s arguments through the Contextualization offered in Step 1.\nStep 3 - Audience: Compose a substantive assessment of the intended audience of the Primary Source. Note how this audience would shape the Primary Source's reception and historical impact in light of the Contextualization offered in Step 1.\nStep 4 - Historiographical Interpretation: Provide a substantive and incisive interpretation of how at least three specific schools of historiographical thought would interpret this source. Compare and contrast how this source could be interpreted by three different academic historiographical schools.  Different historiographical approaches could include: "

                    histriography_options = "Progressive, Consensus, Marxist, postmodern, social history, political history, gender history, and cultural history."
                    instructions = "Instructions: Based on the Historical Method outlined above, provide a substantive and detailed analysis of the Primary Source in the manner of an academic historian. Let's take this step by step, and be sure to include every step."

                    st.header('Primary Source - "The Hayseed" (1890)')

                    hayseed_lyrics = 'I was once a tool of oppression\nAnd as green as a sucker could be\nAnd monopolies banded together\nTo beat a poor hayseed like me.\n"The railroads and old party bosses\nTogether did sweetly agree;\nAnd they thought there would be little trouble\nIn working a hayseed like me. . . ."'
                    source_information = "Source Information: The Primary Source is an American political campaign song called 'The Hayseed,' published in 1890 by a Nebraska newspaper known as the Farmer's Alliance."

                    st.image(image='./hayseed.png')
                    st.write("Arthur L. Kellog, “The Hayseed,” Farmers Alliance (4 October 1890). Nebraska Newspapers (University of Nebraska Libraries), [link.](https://nebnewspapers.unl.edu/lccn/2017270209/1890-10-04/ed-1/seq-1/)")
                    st.write(hayseed_lyrics)
                    st.write(source_information)


                    submit_button_1 = st.form_submit_button(label='Analyze Source')

                    if submit_button_1:

                        primary_source_analysis = prompt + "\n" + historical_method + histriography_options + ".\n\n" + "Primary Source: " + "\n" + hayseed_lyrics + "\n" + source_information + "\n" + instructions + "\n"

                        os.environ["OPENAI_API_KEY"] = st.secrets["openai_api_key"]
                        now = dt.now()

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
                            st.write("GPT-3's Analysis:")
                            st.write(output)
                            #st.write("\n\n\n\n")
                            #st.subheader('As Lord Bacon says, "Truth will sooner come out from error than from confusion."  Please click on the Rank Bacon button above to rank this reply for future improvement.')
                        elif int(filter_function()) == 2:
                            st.write("The OpenAI content filter ranks Bacon's response as potentially offensive. Per OpenAI's use policies, potentially offensive responses will not be displayed.")

                        st.write("\n\n\n\n")
                        st.write("OpenAI's Content Filter Ranking: " +  output_label)

                        def total_output_collection():
                            d1 = {'question':[question], 'histriographies':[histriography_options], 'output':[output], 'filter_ranking':[output_label], 'date':[now]}
                            df1 = pd.DataFrame(data=d1, index=None)
                            sh1 = gc.open('total_outputs_primary_sources')
                            wks1 = sh1[0]
                            cells1 = wks1.get_all_values(include_tailing_empty_rows=False, include_tailing_empty=False, returnas='matrix')
                            end_row1 = len(cells1)
                            wks1.set_dataframe(df1,(end_row1+1,1), copy_head=False, extend=True)

                        def output_collection_filtered():
                            d2 = {'question':[question], 'histriographies':[histriography_options], 'output':[output], 'filter_ranking':[output_label], 'date':[now]}
                            df2 = pd.DataFrame(data=d2, index=None)
                            sh2 = gc.open('primary_source_outputs_filtered')
                            wks2 = sh2[0]
                            cells2 = wks2.get_all_values(include_tailing_empty_rows=False, include_tailing_empty=False, returnas='matrix')
                            end_row2 = len(cells2)
                            wks2.set_dataframe(df2,(end_row2+1,1), copy_head=False, extend=True)

                        def temp_output_collection():
                            d3 = {'question':[question], 'histriographies':[histriography_options], 'output':[output], 'filter_ranking':[output_label], 'date':[now]}
                            df3 = pd.DataFrame(data=d3, index=None)
                            sh3 = gc.open('primary_source_temp')
                            wks3 = sh3[0]
                            wks3.set_dataframe(df3,(1,1))

                        if int(filter_function()) == 2:
                            output_collection_filtered()
                            total_output_collection()
                        else:
                            temp_output_collection()
                            total_output_collection()


        def household_question():
            with col1:
                with st.form('Household Question'):

                    question = "Household Management"
                    prompt = "You are an AI historian specializing in primary source analysis and historiographical interpretation. When given a Primary Source, you will provide a detailed and substantive analysis of that source based on the Historical Method and Source Information below."
                    historical_method = "Step 1 -  Contextualization: Apply the Source Information to provide a lengthy, detailed, and substantive analysis of how the Primary Source reflects the larger historical period in which it was created. In composing this lengthy, detailed, and substantive analysis, note specific events, personalities, and ideologies that shaped the the period noted in the Source Information.\nStep 2 - Purpose : Offer a substantive exploration of the purpose of the Primary Source, interpreting the author’s arguments through the Contextualization offered in Step 1.\nStep 3 - Audience: Compose a substantive assessment of the intended audience of the Primary Source. Note how this audience would shape the Primary Source's reception and historical impact in light of the Contextualization offered in Step 1.\nStep 4 - Historiographical Interpretation: Provide a substantive and incisive interpretation of how at least three specific schools of historiographical thought would interpret this source. Compare and contrast how this source could be interpreted by three different academic historiographical schools.  Different historiographical approaches could include: "

                    histriography_options = "Marxist history, British history, economic history, gender history, labor history, women's history, social history, and the history of marriage."

                    instructions = "Instructions: Based on the Historical Method outlined above, provide a substantive and detailed analysis of the Primary Source in the manner of an academic historian. Let's take this step by step, and be sure to include every step."

                    st.header('Primary Source - "The Book of Household Management" (1861)')

                    hayseed_lyrics = '"As with a Commander of the Army, or leader of any enterprise, so it is with the mistress of the house. Her spirit will be seen through the whole establishment; and just in proportion as she performs her duties intelligently and thoroughly, so will her domestics follow in her path. Of all of those acquirements, which more particularly belong to the feminine character, there are none which take a higher rank, in our estimation, than such as enter into a knowledge of household duties; for on these are perpetually dependent the happiness, comfort, and well-being of the family.'
                    source_information = "Source Information: The Primary Source is The Book of Household Management, published in London in 1861 and written by Isabella Beeton."

                    st.image(image='./household_management.png',  use_column_width='never')
                    st.write("Isabella Beeton, Book of Household Management (S.O. Beeton: London, 1861), 46. Avaliable via the Internet Archive, [link.](https://archive.org/details/b20392758/page/n45/mode/2up)")
                    st.write(hayseed_lyrics)
                    st.write(source_information)

                    submit_button_1 = st.form_submit_button(label='Analyze Source')

                    if submit_button_1:

                        os.environ["OPENAI_API_KEY"] = st.secrets["openai_api_key"]
                        now = dt.now()


                        primary_source_analysis = prompt + "\n" + historical_method + histriography_options + "\n\n" + "Primary Source: " + "\n" + hayseed_lyrics + "\n" + source_information + "\n" + instructions + "\n"

                        os.environ["OPENAI_API_KEY"] = st.secrets["openai_api_key"]
                        now = dt.now()

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
                            st.write("GPT-3's Analysis:")
                            st.write(output)
                            #st.write("\n\n\n\n")
                            #st.subheader('As Lord Bacon says, "Truth will sooner come out from error than from confusion."  Please click on the Rank Bacon button above to rank this reply for future improvement.')
                        elif int(filter_function()) == 2:
                            st.write("The OpenAI content filter ranks Bacon's response as potentially offensive. Per OpenAI's use policies, potentially offensive responses will not be displayed.")

                        st.write("\n\n\n\n")
                        st.write("OpenAI's Content Filter Ranking: " +  output_label)

                        def total_output_collection():
                            d1 = {'question':[question], 'histriographies':[histriography_options], 'output':[output], 'filter_ranking':[output_label], 'date':[now]}
                            df1 = pd.DataFrame(data=d1, index=None)
                            sh1 = gc.open('total_outputs_primary_sources')
                            wks1 = sh1[0]
                            cells1 = wks1.get_all_values(include_tailing_empty_rows=False, include_tailing_empty=False, returnas='matrix')
                            end_row1 = len(cells1)
                            wks1.set_dataframe(df1,(end_row1+1,1), copy_head=False, extend=True)

                        def output_collection_filtered():
                            d2 = {'question':[question], 'histriographies':[histriography_options], 'output':[output], 'filter_ranking':[output_label], 'date':[now]}
                            df2 = pd.DataFrame(data=d2, index=None)
                            sh2 = gc.open('primary_source_outputs_filtered')
                            wks2 = sh2[0]
                            cells2 = wks2.get_all_values(include_tailing_empty_rows=False, include_tailing_empty=False, returnas='matrix')
                            end_row2 = len(cells2)
                            wks2.set_dataframe(df2,(end_row2+1,1), copy_head=False, extend=True)

                        def temp_output_collection():
                            d3 = {'question':[question], 'histriographies':[histriography_options], 'output':[output], 'filter_ranking':[output_label], 'date':[now]}
                            df3 = pd.DataFrame(data=d3, index=None)
                            sh3 = gc.open('primary_source_temp')
                            wks3 = sh3[0]
                            wks3.set_dataframe(df3,(1,1))

                        if int(filter_function()) == 2:
                            output_collection_filtered()
                            total_output_collection()
                        else:
                            temp_output_collection()
                            total_output_collection()

        def lin_zexu_1():
            with col1:
                with st.form('lin_letter'):

                    question = "Lin Zexu to Victoria"
                    prompt = "You are an AI historian specializing in primary source analysis and historiographical interpretation. When given a Primary Source, you will provide a detailed and substantive analysis of that source based on the Historical Method and Source Information below."
                    historical_method = "Step 1 -  Contextualization: Apply the Source Information to provide a lengthy, detailed, and substantive analysis of how the Primary Source reflects the larger historical period in which it was created. In composing this lengthy, detailed, and substantive analysis, note specific events, personalities, and ideologies that shaped the the period noted in the Source Information.\nStep 2 - Purpose : Offer a substantive exploration of the purpose of the Primary Source, interpreting the author’s arguments through the Contextualization offered in Step 1.\nStep 3 - Audience: Compose a substantive assessment of the intended audience of the Primary Source. Note how this audience would shape the Primary Source's reception and historical impact in light of the Contextualization offered in Step 1.\nStep 4 - Historiographical Interpretation: Provide a substantive and incisive interpretation of how at least three specific schools of historiographical thought would interpret this source. Compare and contrast how this source could be interpreted by three different academic historiographical schools.  Different historiographical approaches could include: "

                    histriography_options = "Marxist, postcolonial, World Systems Theory, social history, history of medicine, Diplomatic history, economic history."

                    instructions = "Instructions: Based on the Historical Method outlined above, provide a substantive and detailed analysis of the Primary Source in the manner of an academic historian. Let's take this step by step, and be sure to include every step."

                    st.header('Primary Source - Translation of a letter from Lin Zexu to Queen Victoria (1839)')

                    hayseed_lyrics = '"By what principle of reason then, should these foreigners send in return a poisonous drug? Without meaning to say that the foreigners harbor such destructive intentions in their hearts, we yet positively assert that from their inordinate thirst after gain, they are perfectly careless about the injuries they inflict upon us! And such being the case, we should like to ask what has become of that conscience which heaven has implanted in the breasts of all men? We have heard that in your own country opium is prohibited with the utmost strictness and severity. This is a strong proof that you know full well how hurtful it is to mankind. Since you do not permit it to injure your own country, you ought not to have this injurious drug transferred to another country, and above all others, how much less to the Inner Land! Of the products which China exports to your foreign countries, there is not one which is not beneficial to mankind in some shape or other."'
                    source_information = "Source Information: The Primary Source is a translation of an 1839 letter from Lin Zexu, the Chinese trade commissioner, to Queen Victoria of England."

                    st.image(image='./lin_letter.jpg')
                    st.write("Source: Elijah Coleman Bridgman and Samuel Wells Williams. The Chinese Repository, Volume 8 (Canton, 1840). Avaliable via Google Books, [link.](https://books.google.com/books?id=ngMMAAAAYAAJ&lpg=PR5&pg=PA499#v=onepage&q&f=false)")
                    st.write(hayseed_lyrics)
                    st.write(source_information)

                    submit_button_1 = st.form_submit_button(label='Analyze Source')
                        #with st.expander("Test:"):
                            #test = st.radio("Test",["test1", "test2"])

                    if submit_button_1:

                        os.environ["OPENAI_API_KEY"] = st.secrets["openai_api_key"]
                        now = dt.now()

                        primary_source_analysis = prompt + "\n" + historical_method + "\n\n" + histriography_options + "Primary Source: " + "\n" + hayseed_lyrics + "\n" + source_information + "\n" + instructions

                        os.environ["OPENAI_API_KEY"] = st.secrets["openai_api_key"]
                        now = dt.now()

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
                            st.write("GPT-3's Analysis:")
                            st.write(output)
                            #st.write("\n\n\n\n")
                            #st.subheader('As Lord Bacon says, "Truth will sooner come out from error than from confusion."  Please click on the Rank Bacon button above to rank this reply for future improvement.')
                        elif int(filter_function()) == 2:
                            st.write("The OpenAI content filter ranks Bacon's response as potentially offensive. Per OpenAI's use policies, potentially offensive responses will not be displayed.")

                        st.write("\n\n\n\n")
                        st.write("OpenAI's Content Filter Ranking: " +  output_label)

                        def total_output_collection():
                            d1 = {'question':[question], 'histriographies':[histriography_options], 'output':[output], 'filter_ranking':[output_label], 'date':[now]}
                            df1 = pd.DataFrame(data=d1, index=None)
                            sh1 = gc.open('total_outputs_primary_sources')
                            wks1 = sh1[0]
                            cells1 = wks1.get_all_values(include_tailing_empty_rows=False, include_tailing_empty=False, returnas='matrix')
                            end_row1 = len(cells1)
                            wks1.set_dataframe(df1,(end_row1+1,1), copy_head=False, extend=True)

                        def output_collection_filtered():
                            d2 = {'question':[question], 'histriographies':[histriography_options], 'output':[output], 'filter_ranking':[output_label], 'date':[now]}
                            df2 = pd.DataFrame(data=d2, index=None)
                            sh2 = gc.open('primary_source_outputs_filtered')
                            wks2 = sh2[0]
                            cells2 = wks2.get_all_values(include_tailing_empty_rows=False, include_tailing_empty=False, returnas='matrix')
                            end_row2 = len(cells2)
                            wks2.set_dataframe(df2,(end_row2+1,1), copy_head=False, extend=True)

                        def temp_output_collection():
                            d3 = {'question':[question], 'histriographies':[histriography_options], 'output':[output], 'filter_ranking':[output_label], 'date':[now]}
                            df3 = pd.DataFrame(data=d3, index=None)
                            sh3 = gc.open('primary_source_temp')
                            wks3 = sh3[0]
                            wks3.set_dataframe(df3,(1,1))

                        if int(filter_function()) == 2:
                            output_collection_filtered()
                            total_output_collection()
                        else:
                            temp_output_collection()
                            total_output_collection()

        def mary_lease():
            with col1:
                with st.form('lease_speech'):

                    question = "Mary Lease"
                    prompt = "You are an AI historian specializing in primary source analysis and historiographical interpretation. When given a Primary Source, you will provide a detailed and substantive analysis of that source based on the Historical Method and Source Information below."
                    historical_method = "Step 1 -  Contextualization: Apply the Source Information to provide a lengthy, detailed, and substantive analysis of how the Primary Source reflects the larger historical period in which it was created. In composing this lengthy, detailed, and substantive analysis, note specific events, personalities, and ideologies that shaped the the period noted in the Source Information.\nStep 2 - Purpose : Offer a substantive exploration of the purpose of the Primary Source, interpreting the author’s arguments through the Contextualization offered in Step 1.\nStep 3 - Audience: Compose a substantive assessment of the intended audience of the Primary Source. Note how this audience would shape the Primary Source's reception and historical impact in light of the Contextualization offered in Step 1.\nStep 4 - Historiographical Interpretation: Provide a substantive and incisive interpretation of how at least three specific schools of historiographical thought would interpret this source. Compare and contrast how this source could be interpreted by three different academic historiographical schools.  Different historiographical approaches could include: "

                    histriography_options = "Progressive, Consensus, Marxist, postmodern, social history, political history, gender history, and cultural history."

                    instructions = "Instructions: Based on the Historical Method outlined above, provide a substantive and detailed analysis of the Primary Source in the manner of an academic historian. Let's take this step by step, and be sure to include every step."

                    st.header('Primary Source - Mary Lease, "Women in the Farmers Alliance" (1891)')

                    hayseed_lyrics = '"Madame President and Fellow Citizens:— If God were to give me my choice to live in any age of the world that has flown, or in any age of the world yet to be, I would say, O God, let me live here and now, in this day and age of the world’s history. We are living in a grand and wonderful time: we are living in a day when old ideas, old traditions, and old customs have broken loose from their moorings, and are hopelessly adrift on the great shoreless, boundless sea of human thought; we are living in a time when the gray old world begins to dimly comprehend that there is no difference between the brain of an intelligent woman and the brain of an intelligent man; no difference between the soul-power or brain power that nerved the arm of Charlotte Corday to deeds of heroism, and which swayed old John Brown behind his barricade at Ossawattomie; we are living in a day and age when the women of industrial societies and the Alliance women have become a mighty factor in the politics of this nation; when the mighty dynamite of thought is stirring the hearts of men of this world from centre to circumference, and social and political structure and stirring the hearts of men from centre to circumference, and this thought is crystallizing into action.'
                    source_information = 'Source Information: The Primary Source is a speech entitled "Women in the Farmers Alliance" given by Mary Lease to the National Council of Women National Meeting in Washington D.C. in 1891.'

                    st.image(image='./lease.png')
                    st.write("Source: National Council of Women of the United States, Transactions of the National Council of Women of the United States: Assembled in Washington, D.C., February 22 to 25, 1891. Avaliable via Google Books, [link.](https://books.google.com/books?id=bpU0xGnVETsC&newbks=1&newbks_redir=0&dq=If%20God%20were%20to%20give%20me%20my%20choice%20to%20live%20in%20any%20age%20of%20the%20world%20that%20has%20flown%2C%20or%20in%20any%20age%20of%20the%20world%20yet%20to%20be%2C%20I%20would%20say%2C%20O%20God%2C%20let%20me%20live%20here%20and%20now%2C%20in%20this%20day%20and%20age%20of%20the%20world%E2%80%99s%20history.&pg=PA214#v=onepage&q&f=false)")
                    st.write(hayseed_lyrics)
                    st.write(source_information)

                    submit_button_1 = st.form_submit_button(label='Analyze Source')
                        #with st.expander("Test:"):
                            #test = st.radio("Test",["test1", "test2"])

                    if submit_button_1:

                        os.environ["OPENAI_API_KEY"] = st.secrets["openai_api_key"]
                        now = dt.now()

                        primary_source_analysis = prompt + "\n" + historical_method + histriography_options + "\n\n" + "Primary Source: " + "\n" + hayseed_lyrics + "\n" + source_information + "\n" + instructions + "\n"

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
                            st.write("GPT-3's Analysis:")
                            st.write(output)
                            #st.write("\n\n\n\n")
                            #st.subheader('As Lord Bacon says, "Truth will sooner come out from error than from confusion."  Please click on the Rank Bacon button above to rank this reply for future improvement.')
                        elif int(filter_function()) == 2:
                            st.write("The OpenAI content filter ranks Bacon's response as potentially offensive. Per OpenAI's use policies, potentially offensive responses will not be displayed.")

                        st.write("\n\n\n\n")
                        st.write("OpenAI's Content Filter Ranking: " +  output_label)

                        def total_output_collection():
                            d1 = {'question':[question], 'histriographies':[histriography_options], 'output':[output], 'filter_ranking':[output_label], 'date':[now]}
                            df1 = pd.DataFrame(data=d1, index=None)
                            sh1 = gc.open('total_outputs_primary_sources')
                            wks1 = sh1[0]
                            cells1 = wks1.get_all_values(include_tailing_empty_rows=False, include_tailing_empty=False, returnas='matrix')
                            end_row1 = len(cells1)
                            wks1.set_dataframe(df1,(end_row1+1,1), copy_head=False, extend=True)

                        def output_collection_filtered():
                            d2 = {'question':[question], 'histriographies':[histriography_options], 'output':[output], 'filter_ranking':[output_label], 'date':[now]}
                            df2 = pd.DataFrame(data=d2, index=None)
                            sh2 = gc.open('primary_source_outputs_filtered')
                            wks2 = sh2[0]
                            cells2 = wks2.get_all_values(include_tailing_empty_rows=False, include_tailing_empty=False, returnas='matrix')
                            end_row2 = len(cells2)
                            wks2.set_dataframe(df2,(end_row2+1,1), copy_head=False, extend=True)

                        def temp_output_collection():
                            d3 = {'question':[question], 'histriographies':[histriography_options], 'output':[output], 'filter_ranking':[output_label], 'date':[now]}
                            df3 = pd.DataFrame(data=d3, index=None)
                            sh3 = gc.open('primary_source_temp')
                            wks3 = sh3[0]
                            wks3.set_dataframe(df3,(1,1))

                        if int(filter_function()) == 2:
                            output_collection_filtered()
                            total_output_collection()
                        else:
                            temp_output_collection()
                            total_output_collection()

        def practical_housekeeping():
            with col1:
                with st.form('practical_housekeeping'):

                    question = "Practical Housekeeping"
                    prompt = "You are an AI historian specializing in primary source analysis and historiographical interpretation. When given a Primary Source, you will provide a detailed and substantive analysis of that source based on the Historical Method and Source Information below."
                    historical_method = "Step 1 -  Contextualization: Apply the Source Information to provide a lengthy, detailed, and substantive analysis of how the Primary Source reflects the larger historical period in which it was created. In composing this lengthy, detailed, and substantive analysis, note specific events, personalities, and ideologies that shaped the the period noted in the Source Information.\nStep 2 - Purpose : Offer a substantive exploration of the purpose of the Primary Source, interpreting the author’s arguments through the Contextualization offered in Step 1.\nStep 3 - Audience: Compose a substantive assessment of the intended audience of the Primary Source. Note how this audience would shape the Primary Source's reception and historical impact in light of the Contextualization offered in Step 1.\nStep 4 - Historiographical Interpretation: Provide a substantive and incisive interpretation of how at least three specific schools of historiographical thought would interpret this source. Compare and contrast how this source could be interpreted by three different academic historiographical schools.  Different historiographical approaches could include the Marxist history, British history, economic history, gender history, labor history, women's history, social history, and the history of marriage."

                    histriography_options = "Marxist history, British history, economic history, gender history, labor history, women's history, social history, and the history of marriage."

                    instructions = "Instructions: Based on the Historical Method outlined above, provide a substantive and detailed analysis of the Primary Source in the manner of an academic historian. Let's take this step by step, and be sure to include every step."

                    st.header('Primary Source - Mrs. Frederick Pauley, Practical Housekeeping (1867)')

                    hayseed_lyrics = "Whatever information the following pages may contain, bears reference to wives who are their own housekeepers. A housekeeper, in the usual acceptance of the word, may be simply to be a paid employee, with no higher aim than a conscientious endeavor to acquit herself honestly of the trust confided to her charge. But a wife who keeps her husband's home has a higher interest at stake. Her responsibilities do not end with the dispensing of stores and checking of accounts. Health and happinness, joy and sorrow, are more or less dependent on the good or evil of her presence. Her rule extends from the attic to the cellar: her influence affects every dweller beneath her roof. She can neighter resign her place, no be dismissed from it, if by mismanagement she loses the confidence of her husband. Her engagement is life-long-'for better for worse, for richer for poorer.'"

                    source_information = "Source Information: The Primary Source is the introduction to Practical Housekeeping, a book published in London in 1867 by Mrs. Frederick Pauley."

                    st.image(image='./practical_housekeeping.png')
                    st.write("Source: Mrs. Frederick Pauley, Practical Housekeeping (Routledge: London, 1867), Google Books, [link](https://books.google.com/books?id=_z4CAAAAQAAJ&newbks=1&newbks_redir=0&dq=Routledge's%20manual%20of%20etiquette&pg=PA1#v=onepage&q&f=false)")
                    st.write(hayseed_lyrics)
                    st.write(source_information)

                    submit_button_1 = st.form_submit_button(label='Analyze Source')
                        #with st.expander("Test:"):
                            #test = st.radio("Test",["test1", "test2"])

                    if submit_button_1:

                        os.environ["OPENAI_API_KEY"] = st.secrets["openai_api_key"]
                        now = dt.now()

                        #model selection for OpenAI query


                        primary_source_analysis = prompt + "\n" + historical_method + histriography_options + "\n\n" + "Primary Source: " + "\n" + hayseed_lyrics + "\n" + source_information + "\n" + instructions + "\n"

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
                            st.write("GPT-3's Analysis:")
                            st.write(output)
                            #st.write("\n\n\n\n")
                            #st.subheader('As Lord Bacon says, "Truth will sooner come out from error than from confusion."  Please click on the Rank Bacon button above to rank this reply for future improvement.')
                        elif int(filter_function()) == 2:
                            st.write("The OpenAI content filter ranks Bacon's response as potentially offensive. Per OpenAI's use policies, potentially offensive responses will not be displayed.")

                        st.write("\n\n\n\n")
                        st.write("OpenAI's Content Filter Ranking: " +  output_label)

                        def total_output_collection():
                            d1 = {'question':[question], 'histriographies':[histriography_options], 'output':[output], 'filter_ranking':[output_label], 'date':[now]}
                            df1 = pd.DataFrame(data=d1, index=None)
                            sh1 = gc.open('total_outputs_primary_sources')
                            wks1 = sh1[0]
                            cells1 = wks1.get_all_values(include_tailing_empty_rows=False, include_tailing_empty=False, returnas='matrix')
                            end_row1 = len(cells1)
                            wks1.set_dataframe(df1,(end_row1+1,1), copy_head=False, extend=True)

                        def output_collection_filtered():
                            d2 = {'question':[question], 'histriographies':[histriography_options], 'output':[output], 'filter_ranking':[output_label], 'date':[now]}
                            df2 = pd.DataFrame(data=d2, index=None)
                            sh2 = gc.open('primary_source_outputs_filtered')
                            wks2 = sh2[0]
                            cells2 = wks2.get_all_values(include_tailing_empty_rows=False, include_tailing_empty=False, returnas='matrix')
                            end_row2 = len(cells2)
                            wks2.set_dataframe(df2,(end_row2+1,1), copy_head=False, extend=True)

                        def temp_output_collection():
                            d3 = {'question':[question], 'histriographies':[histriography_options], 'output':[output], 'filter_ranking':[output_label], 'date':[now]}
                            df3 = pd.DataFrame(data=d3, index=None)
                            sh3 = gc.open('primary_source_temp')
                            wks3 = sh3[0]
                            wks3.set_dataframe(df3,(1,1))

                        if int(filter_function()) == 2:
                            output_collection_filtered()
                            total_output_collection()
                        else:
                            temp_output_collection()
                            total_output_collection()

        def len_letter_2():
            with col1:
                with st.form('lin_letter_2'):

                    question = "Lin Zexu destroys the Opium"
                    prompt = "You are an AI historian specializing in primary source analysis and historiographical interpretation. When given a Primary Source, you will provide a detailed and substantive analysis of that source based on the Historical Method and Source Information below."
                    historical_method = "Step 1 -  Contextualization: Apply the Source Information to provide a lengthy, detailed, and substantive analysis of how the Primary Source reflects the larger historical period in which it was created. In composing this lengthy, detailed, and substantive analysis, note specific events, personalities, and ideologies that shaped the the period noted in the Source Information.\nStep 2 - Purpose : Offer a substantive exploration of the purpose of the Primary Source, interpreting the author’s arguments through the Contextualization offered in Step 1.\nStep 3 - Audience: Compose a substantive assessment of the intended audience of the Primary Source. Note how this audience would shape the Primary Source's reception and historical impact in light of the Contextualization offered in Step 1.\nStep 4 - Historiographical Interpretation: Provide a substantive and incisive interpretation of how at least three specific schools of historiographical thought would interpret this source. Compare and contrast how this source could be interpreted by three different academic historiographical schools.  Different historiographical approaches could include: "
                    histriography_options = "Marxist, postcolonial, World Systems Theory, social history, history of medicine, Diplomatic history, economic history."

                    instructions = "Instructions: Based on the Historical Method outlined above, provide a substantive and detailed analysis of the Primary Source in the manner of an academic historian. Let's take this step by step, and be sure to include every step."

                    st.header('Primary Source - Lin Zexu Burns the Opium (1909)')

                    hayseed_lyrics = "In 1839, Lin Zexu arrived as Governor-general of Liangguang, and discovered that Western merchants held opium stores of 20,283 chests. He burnt them all on the beach. Later other foreign ships secretly stole into port with more opium. Lin took advantage of a dark night when the tide was low to send crack troops to capture them. He burnt 23 ships at Changsha bay. Subsequently, because these actions caused a diplomatic incident, opium imports kept on growing. Now the British government agrees that we must eliminate the poison of opium. Reflecting on past events, we have turned our misfortunes into a happy outcome."

                    source_information = "Source Information: The Primary Source is a translation of “Portraits of the Achievements of Our Dynasty’s Illustrious Officials,” an illustrated print published in the Shanghai newspaper Shishibao Tuhua in 1909."

                    st.image(image='./lin_print.jpg')
                    st.write('Source: Peter Perdue, “Production and Consumption", The First Opium War: The Anglo-Chinese War of 1839-1942. Visualizing Cultures (MIT, 2010), [link](https://visualizingcultures.mit.edu/opium_wars_01/ow1_essay02.html)')
                    st.write(hayseed_lyrics)
                    st.write(source_information)

                    submit_button_1 = st.form_submit_button(label='Analyze Source')
                        #with st.expander("Test:"):
                            #test = st.radio("Test",["test1", "test2"])

                    if submit_button_1:

                        os.environ["OPENAI_API_KEY"] = st.secrets["openai_api_key"]
                        now = dt.now()

                        #model selection for OpenAI query


                        primary_source_analysis = prompt + "\n" + historical_method + histriography_options + "\n\n" + "Primary Source: " + "\n" + hayseed_lyrics + "\n" + source_information + "\n" + instructions

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
                            st.write("GPT-3's Analysis:")
                            st.write(output)
                            #st.write("\n\n\n\n")
                            #st.subheader('As Lord Bacon says, "Truth will sooner come out from error than from confusion."  Please click on the Rank Bacon button above to rank this reply for future improvement.')
                        elif int(filter_function()) == 2:
                            st.write("The OpenAI content filter ranks Bacon's response as potentially offensive. Per OpenAI's use policies, potentially offensive responses will not be displayed.")

                        st.write("\n\n\n\n")
                        st.write("OpenAI's Content Filter Ranking: " +  output_label)

                        def total_output_collection():
                            d1 = {'question':[question], 'histriographies':[histriography_options], 'output':[output], 'filter_ranking':[output_label], 'date':[now]}
                            df1 = pd.DataFrame(data=d1, index=None)
                            sh1 = gc.open('total_outputs_primary_sources')
                            wks1 = sh1[0]
                            cells1 = wks1.get_all_values(include_tailing_empty_rows=False, include_tailing_empty=False, returnas='matrix')
                            end_row1 = len(cells1)
                            wks1.set_dataframe(df1,(end_row1+1,1), copy_head=False, extend=True)

                        def output_collection_filtered():
                            d2 = {'question':[question], 'histriographies':[histriography_options], 'output':[output], 'filter_ranking':[output_label], 'date':[now]}
                            df2 = pd.DataFrame(data=d2, index=None)
                            sh2 = gc.open('primary_source_outputs_filtered')
                            wks2 = sh2[0]
                            cells2 = wks2.get_all_values(include_tailing_empty_rows=False, include_tailing_empty=False, returnas='matrix')
                            end_row2 = len(cells2)
                            wks2.set_dataframe(df2,(end_row2+1,1), copy_head=False, extend=True)

                        def temp_output_collection():
                            d3 = {'question':[question], 'histriographies':[histriography_options], 'output':[output], 'filter_ranking':[output_label], 'date':[now]}
                            df3 = pd.DataFrame(data=d3, index=None)
                            sh3 = gc.open('primary_source_temp')
                            wks3 = sh3[0]
                            wks3.set_dataframe(df3,(1,1))

                        if int(filter_function()) == 2:
                            output_collection_filtered()
                            total_output_collection()
                        else:
                            temp_output_collection()
                            total_output_collection()


        with st.sidebar.form(key ='Form2'):
            st.write("The following experiment pairs topically similar primary sources, one drawn from the A.P. curriculum and one from outside it. You are invited to rank GPT-3's responses. The rankings will help provide research data on GPT-3 performance.")
            field_choice = st.radio("Choose a Primary Source:", ['"The Hayseed" (U.S. History)', '"Women in the Farmers Alliance" (U.S. History)', '"Book of Household Management" (European History)', '"Practical Housekeeping" (European History)', 'A letter from Lin Zexu to Queen Victoria (World History)', 'Lin Zexu Burns the Opium (World History)'])

            button2 = st.form_submit_button("Click here to load the Primary Source.")

            if field_choice == '"The Hayseed" (U.S. History)':
                field_choice = hayseed_question()
            elif field_choice == '"Women in the Farmers Alliance" (U.S. History)':
                field_choice = mary_lease()
            elif field_choice == '"Book of Household Management" (European History)':
                field_choice = household_question()
            elif field_choice == '"Practical Housekeeping" (European History)':
                field_choice = practical_housekeeping()
            elif field_choice == 'A letter from Lin Zexu to Queen Victoria (World History)':
                field_choice = lin_zexu_1()
            elif field_choice == 'Lin Zexu Burns the Opium (World History)':
                field_choice = len_letter_2()


            st.write("")

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
