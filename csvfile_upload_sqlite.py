import streamlit as st
import os
import pandas as pd
import google.generativeai as genai
import pyaudio
import wave
from dotenv import load_dotenv
import whisper
import re
import pandasql as ps

# Set the PATH for ffmpeg
os.environ['PATH'] += os.pathsep + r'C:\jcffmpeg\bin'

# Set the page configuration
st.set_page_config(page_title="SQL Query Retrieval App", layout="centered")

# Custom CSS for a fancy background
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #74ebd5, #ACB6E5);  /* Gradient background */
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    h1, h2, h3, h4, h5, h6 {
        color: #333333;  /* Sets a darker color for headers */
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);  /* Adds a subtle text shadow for clarity */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Load environment variables
load_dotenv()

# Function to record audio
def record(output_filename):

    st.info("Mock recording...Using pre-recorded audio.")
    # Use a pre-recorded audio file or generate dummy data
    with open("output1.wav", "rb") as f:
        audio_data = f.read()
    with wave.open(output_filename, 'wb') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(44100)
        wf.writeframes(audio_data)

    st.success("Mock recording completed!")


# Function to transcribe audio
def transcribe_audio(input_file):
    model = whisper.load_model("base")
    result = model.transcribe(input_file)
    return result["text"]

# Configure GenAI key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Function to load Google Gemini Model and provide queries as response
def get_gemini_response(question, prompt):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content([prompt[0], question])
    return response.text

# Function to retrieve query from the DataFrame using eval
def read_sql_query(sql, df):
    try:
        result_df = ps.sqldf(sql, locals())
        return result_df
    except Exception as e:
        st.error(f"Query error: {e}")
        return pd.DataFrame()

# Streamlit App
st.title("SpeakSQL: App to Retrieve Data")

# File uploader for CSV


st.markdown("### Record your question")
st.markdown("Press the button below to start recording your question.")

if 'transcription' not in st.session_state:
    st.session_state.transcription = ""

if st.button("Record"):
    with st.spinner("Recording... Please wait."):
        record('output1.wav')
        st.success("Recording completed!")
        st.session_state.transcription = transcribe_audio('output1.wav')

transcription = st.text_area("Input Question", value=st.session_state.transcription, height=100)


uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df_name = "df"  # Name for the dataframe in the prompt
    st.write("Data loaded successfully:")
    st.dataframe(df.head())

    # Dynamically create the prompt based on the DataFrame columns
    columns = ', '.join(df.columns)
    prompt = [
        f"""
        You are an expert in converting English questions to SQL query!
        The SQL database has the name {df_name} and has the following columns - {columns}.

        For example:
        Example 1 - How many entries of records are present?, the SQL command will be something like this:
        SELECT COUNT(*) FROM {df_name};

        Example 2 - Tell me all the entries where {df.columns[0]} is equal to "value", the SQL command will be something like this:
        SELECT * FROM {df_name} WHERE {df.columns[0]}="value";

        Please do not include ``` at the beginning or end and the SQL keyword in the output.
        """
    ]

    if st.button("Click here to display results"):
        with st.spinner("Generating SQL query..."):
            response = get_gemini_response(transcription, prompt)
            st.success("SQL query generated!")

        sql_query = response.strip().split(';')[0].strip()

        st.code(sql_query, language='sql')

        with st.spinner("Executing SQL query..."):
            try:
                result = read_sql_query(sql_query, df)
                st.success("Query executed!")
                st.subheader("Query Results")
                st.dataframe(result)
            except Exception as e:
                st.error(f"Query error: {e}")
else:
    st.write("Please upload a CSV file to proceed.")
