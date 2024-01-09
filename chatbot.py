import streamlit as st
from openai import OpenAI
import re
from prompts import get_system_prompt, get_table_context
from education import load_data_from_snowflake, clean_data, perform_eda, create_visualizations, interactive_data_filter, train_and_evaluate_model

st.title("📖 EduRegion Explorer")

st.sidebar.title("User Guide")
with st.sidebar.expander("How to Use This App"):
    st.markdown("""
    **Welcome to EduRegion Explorer!** Here's how to get started:

    - **Selecting a Dataset**: Choosing the dataset which is approved (Education Regional dataset) from dataGov "https://data.gov.in/resource/state-wise-male-and-female-student-enrolment-regional-centers-university-offering-0" to explore its features.
    - **Chatbot Interaction**: Ask questions in natural language to get insights. For example, 'Show total enrollment by gender for Alagappa University'.
    - **Data Cleaning**: Use the 'Clean Data' checkbox to prepare your data for analysis.
    - **Exploratory Data Analysis**: Explore various aspects of the data through the EDA section.
    - **Visualizations**: Create and view different types of charts that represent the data.
    - **Machine Learning Model**: Run the enrollment prediction model after cleaning the data.
    - **LLM Model**:If you have any questions related to databases and queries,ask questions to my LLM model named EduRegion Explorer.
                
    For more detailed instructions, visit [https://docs.google.com/document/d/1nZ3t8uWRJzpaNmevyY-Skcaqg4Lm_oDJ/edit?usp=sharing&ouid=112835967963675916698&rtpof=true&sd=true].
    """)

# Sidebar for Machine Learning Features
st.sidebar.title("Additional Machine Learning Features")
with st.sidebar:
    if st.checkbox("Show Machine Learning Features"):
        st.subheader("Machine Learning Features")
        
        # Initialize session state variables for data
        if 'data' not in st.session_state:
            st.session_state.data = None
        if 'data_cleaned' not in st.session_state:
            st.session_state.data_cleaned = False

        # Load Data
        if st.button("Load Data"):
            st.session_state.data = load_data_from_snowflake()

        # Data Cleaning
        if st.session_state.data is not None and st.button("Clean Data"):
            st.session_state.data = clean_data(st.session_state.data)
            st.session_state.data_cleaned = True

        # Exploratory Data Analysis
        if st.session_state.data_cleaned and st.checkbox("Perform EDA"):
            perform_eda(st.session_state.data)

        # Interactive Data Filter
        if st.session_state.data_cleaned and st.checkbox("Interactive Data Filter"):
            interactive_data_filter(st.session_state.data)

        # Data Visualizations
        if st.session_state.data_cleaned and st.checkbox("Create Visualizations"):
            create_visualizations(st.session_state.data)

        # Run Enrollment Prediction Model
        if st.session_state.data_cleaned and st.checkbox("Run Enrollment Prediction Model"):
            mse, r2, accuracy_percentage, model_name = train_and_evaluate_model(st.session_state.data)
            st.write(f"Algorithm used for prediction: {model_name}")
            st.write(f"Model Mean Squared Error: {mse}")
            st.write(f"Model R² Score: {r2}")
            st.write(f"Model Accuracy: {accuracy_percentage:.2f}%")

# Initialize the chat messages history
client = OpenAI(api_key=st.secrets.OPENAI_API_KEY)

def add_bg_from_url():
    st.markdown(f"""
         <style>
         .stApp {{
             background-image: url("https://img.freepik.com/free-photo/gray-abstract-wireframe-technology-background_53876-101941.jpg?w=996&t=st=1662725888~exp=1662726488~hmac=3b148d7688fd138851b5a25f611ca9cf08bf2d28382e218d5896f95f6baa2bd4");
             background-attachment: fixed;
             background-size: cover}}
             </style>""",unsafe_allow_html=True)
add_bg_from_url() 

# Initialize session state variables if they don't exist
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'dataset_choice' not in st.session_state:
    st.session_state.dataset_choice = None
if 'last_dataset_choice' not in st.session_state:
    st.session_state.last_dataset_choice = None

# Define a function to update the system prompt based on dataset choice
def update_system_prompt(dataset_choice):
    if dataset_choice and dataset_choice != 'Select a dataset':
        st.session_state.messages = [{"role": "system", "content": get_system_prompt(dataset_choice)}]

# User selects the dataset
dataset_options = ['Select a dataset', 'Regional University Enrollment Data', 'Australian Educational Institutions Insights']
selected_option = st.selectbox("Select Dataset:", dataset_options, index=0)

# Update dataset_choice in session state when user makes a selection
if selected_option != 'Select a dataset':
    if st.session_state.dataset_choice != selected_option:
        st.session_state.dataset_choice = selected_option
        update_system_prompt(selected_option)

# Prompt for user input and save
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})

# Display the existing chat messages
for message in st.session_state.messages:
    if message["role"] == "system":
        continue
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if "results" in message:
            st.dataframe(message["results"])

# Generate a new response if the last message is not from the assistant
if st.session_state.messages and st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        response = ""
        resp_container = st.empty()
        for delta in client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
            stream=True,
        ):
            response += (delta.choices[0].delta.content or "")
            resp_container.markdown(response)

        message = {"role": "assistant", "content": response}
        # Parse the response for a SQL query and execute if available
        sql_match = re.search(r"```sql\n([\s\S]*?)\n```", response, re.DOTALL)  # Adjusted regex
        if sql_match:
            sql_query = sql_match.group(1)
            try:
                # Execute the SQL query and display results
                conn = st.connection("snowflake")
                query_result = conn.query(sql_query)
                st.dataframe(query_result)

            except Exception as e:
                st.error("The provided query could not be executed. Please ensure it is relevant to the selected dataset.")

        st.session_state.messages.append(message)

# Collecting User Feedback
st.sidebar.title("Feedback")
rating = st.sidebar.slider("Rate your experience", 1, 5, 3)
if st.sidebar.button("Submit Rating"):
    st.sidebar.success(f"Thanks for rating us {rating} stars!")
    # Logic to store the rating
    st.sidebar.markdown(
    "Do visit my [Github Repository](https://github.com/MohamedFarhun/StockMarketAnalysis)"
) 
