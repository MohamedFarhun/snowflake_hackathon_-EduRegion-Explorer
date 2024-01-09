# Import necessary libraries
import streamlit as st
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score

def load_data_from_snowflake():
    # Define the table name from your Snowflake database
    table_name = "HACKATHONS.EDUCATION_ANALYSIS.EDUCATIONAL_ENTITY_ENROLLMENT_SUMMARY"

    # Establish a connection to Snowflake
    conn = st.connection("snowflake")

    # Query the table and load data
    query = f"SELECT * FROM {table_name}"
    data = conn.query(query)

    st.dataframe(data.head())
    return data

# Function for data cleaning
def clean_data(data):
    st.subheader('Data Cleaning')
    # Checking for missing values
    missing_values = data.isnull().sum()

    # Verifying data types
    data_types = data.dtypes

    # Checking for duplicate entries
    duplicate_entries = data.duplicated().sum()

     # Data Cleaning Summary
    cleaning_summary = {
    "Missing Values": missing_values,
    "Data Types": data_types,
    "Duplicate Entries": duplicate_entries
    }
    st.dataframe(cleaning_summary)
    st.session_state.data_cleaned = True
    return data

# Function for Exploratory Data Analysis
def perform_eda(data):

    # Descriptive statistics
    st.write("Descriptive Statistics:")
    st.dataframe(data.describe())

    # Breakdown of enrollment by course level
    st.write("Enrollment by Course Level:")
    enrollment_by_level = data.groupby('LEVEL')[['TOTAL_MALE_ENROLLMENT', 'TOTAL_FEMALE_ENROLLMENT', 'TOTAL_ENROLLMENT']].sum()
    st.dataframe(enrollment_by_level)

# Function for creating visualizations
def create_visualizations(data):
    import matplotlib.pyplot as plt
    import seaborn as sns

    # EDA 1: Distribution of courses by state
    state_course_distribution = data['UNIVERSITY_STATE'].value_counts()

    # EDA 2: Enrollment trends by gender
    total_male_enrollment = data['TOTAL_MALE_ENROLLMENT'].sum()
    total_female_enrollment = data['TOTAL_FEMALE_ENROLLMENT'].sum()

    # EDA 3: Comparison of course levels in terms of total enrollment
    course_level_enrollment = data.groupby('LEVEL')['TOTAL_ENROLLMENT'].sum().sort_values(ascending=False)

    # Visualization
    plt.figure(figsize=(12, 6))
    plt.subplot(2, 1, 1)
    state_course_distribution.plot(kind='bar')
    plt.title('Distribution of Courses by State')
    plt.xlabel('State')
    plt.ylabel('Number of Courses')

    plt.subplot(2, 1, 2)
    labels = ['Male', 'Female']
    sizes = [total_male_enrollment, total_female_enrollment]
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.axis('equal')  
    plt.title('Enrollment Trends by Gender')

    # State-wise total enrollment
    st.write("State-wise Total Enrollment:")
    state_wise_enrollment = data.groupby('UNIVERSITY_STATE')['TOTAL_ENROLLMENT'].sum()
    st.bar_chart(state_wise_enrollment)

    plt.tight_layout()
    st.pyplot(plt)
    plt.close()
    pass

# Function for Interactive Data Filter
def interactive_data_filter(data):
    st.subheader("Interactive Data Filter")

    # User selects a state (None as default)
    state = st.selectbox("Select a State", options=[None] + list(data['UNIVERSITY_STATE'].unique()))

    # Only filter and show data if a state is selected
    if state is not None:
        # Data filtered based on the state selection
        filtered_data = data[data['UNIVERSITY_STATE'] == state]
        
        # Displaying filtered data
        st.dataframe(filtered_data)

        # Further analysis and visualizations on the filtered data
        # Example: Gender distribution in the selected state
        if st.checkbox(f"Show Gender Distribution in {state}"):
            gender_distribution_state = filtered_data.groupby('LEVEL')[['TOTAL_MALE_ENROLLMENT', 'TOTAL_FEMALE_ENROLLMENT']].sum()
            st.bar_chart(gender_distribution_state)

# Function to encode categorical variables for the model
def encode_categorical(data):
    # Example: Convert 'State of University' to numeric codes
    data['State_Code'] = data['UNIVERSITY_STATE'].astype('category').cat.codes
    return data

# Function to prepare data for modeling
def prepare_data_for_modeling(data):
    # Encoding categorical variables
    data = encode_categorical(data)
    
    # Selecting features and target
    X = data[['State_Code', 'TOTAL_MALE_ENROLLMENT', 'TOTAL_FEMALE_ENROLLMENT']]  # Add more features as needed
    y = data['TOTAL_ENROLLMENT']
    
    return train_test_split(X, y, test_size=0.3, random_state=42)

# Function to train and evaluate the model
def train_and_evaluate_model(data):
    X_train, X_test, y_train, y_test = prepare_data_for_modeling(data)
    
    # Training the model
    model = LinearRegression()
    model.fit(X_train, y_train)

    # Predicting and evaluating
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    # Get the model's name
    model_name = type(model).__name__
    
    # Considering R² as the 'accuracy' of the regression model
    accuracy_percentage = r2 * 100

    return mse, r2,accuracy_percentage,model_name

if 'data_cleaned' not in st.session_state:
    st.session_state.data_cleaned = False

# Streamlit App
def main():
    st.title('SnowFlake Hackathon')
    st.header('Theme :- Education')
    st.header("Problem statement :- Education in Regional Languages Data Analysis")

    # Replace load_data() with load_data_from_snowflake()
    st.subheader('State-wise male and female student enrolment in regional centers of university dataset')
    data = load_data_from_snowflake()
    # Clean Data checkbox
    if st.checkbox('Clean Data'):
        data_clean = clean_data(data)

    st.subheader("Exploratory Data Analysis")
    perform_eda(data_clean)

    # Call to the interactive data filter function
    st.subheader('Interactive Data Analysis')
    interactive_data_filter(data_clean)

    st.subheader("Data Visualizations")
    create_visualizations(data_clean)

    if st.checkbox("Run Enrollment Prediction Model"):
        if st.session_state.data_cleaned:
            mse, r2,accuracy_percentage,model_name = train_and_evaluate_model(data_clean)
            st.write(f"Algorithm used for prediction: {model_name}")
            st.write(f"Model Mean Squared Error: {mse}")
            st.write(f"Model R² Score: {r2}")
            st.write(f"Model Accuracy : {accuracy_percentage:.2f}%")
        else:
            # Prompt the user to clean the data first
            st.error("Please check the 'Clean Data' checkbox and re-run the analysis before running the prediction model.")

if __name__ == "__main__":
    main()