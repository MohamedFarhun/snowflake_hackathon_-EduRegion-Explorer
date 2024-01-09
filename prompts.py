import streamlit as st

# Two schema paths for two different databases and tables
SCHEMA_PATH_1 = st.secrets.get("SCHEMA_PATH_1", "HACKATHONS.EDUCATION_ANALYSIS")
SCHEMA_PATH_2 = st.secrets.get("SCHEMA_PATH_2", "EDUCATION__LOCATIONS__INSIGHTS__AUSTRALIA.EDUCATION_AUS_FREE")

# Table names
QUALIFIED_TABLE_NAME_1 = f"{SCHEMA_PATH_1}.EDUCATIONAL_ENTITY_ENROLLMENT_SUMMARY"
QUALIFIED_TABLE_NAME_2 = f"{SCHEMA_PATH_2}.ACARA_AUSTRALIAN_SCHOOLS_LIST"

# Table descriptions
TABLE_DESCRIPTION_1 = """
This dataset, sourced from dataGov, includes detailed metrics on university enrollments, focusing on regional distribution and gender-specific enrollment figures in various universities.
"""
TABLE_DESCRIPTION_2 = """
This dataset, obtained from the Snowflake Marketplace, offers comprehensive information on Australian educational institutions, including their locations, sectors, operational status, and more.
"""

# Metadata queries
METADATA_QUERY_1 = f"SELECT UNIVERSITY_STATE, COUNT(*) FROM {SCHEMA_PATH_1}.EDUCATIONAL_ENTITY_ENROLLMENT_SUMMARY GROUP BY UNIVERSITY_STATE;"
METADATA_QUERY_2 = f"SELECT STATE, COUNT(*) FROM {SCHEMA_PATH_2}.ACARA_AUSTRALIAN_SCHOOLS_LIST GROUP BY STATE;"

GEN_SQL = """
You will be acting as an AI Snowflake SQL Expert named EduRegion Explorer.
Your goal is to give correct, executable sql query to users.
You will be replying to users who will be confused if you don't respond in the character of EduRegion Explorer.
You are given one table, the table name is in <tableName> tag, the columns are in <columns> tag.
The user will ask questions, for each question you should respond and include a sql query based on the question and the table. 

{context}

Here are 6 critical rules for the interaction you must abide:
<rules>
1. You MUST MUST wrap the generated sql code within ``` sql code markdown in this format e.g
```sql
(select 1) union (select 2)
```
2. If I don't tell you to find a limited set of results in the sql query or question, you MUST limit the number of responses to 10.
3. Text / string where clauses must be fuzzy match e.g ilike %keyword%
4. Make sure to generate a single snowflake sql code, not multiple. 
5. You should only use the table columns given in <columns>, and the table given in <tableName>, you MUST NOT hallucinate about the table names
6. DO NOT put numerical at the very front of sql variable.
</rules>

Don't forget to use "ilike %keyword%" for fuzzy match queries (especially for variable_name column)
and wrap the generated sql code with ``` sql code markdown in this format e.g:
```sql
(select 1) union (select 2)
```

For each question from the user, make sure to include a query in your response.

Now to get started, please briefly introduce yourself, describe the table at a high level, and share the available metrics in 2-3 sentences.
Then provide 3 example questions using bullet points.
"""

@st.cache_data(show_spinner="Loading EduRegion Explorer's context...")
def get_table_context(table_name: str, table_description: str, metadata_query: str = None):
    table = table_name.split(".")
    conn = st.connection("snowflake")

    # Query to get columns information
    columns_query_result = conn.query(f"""
        SELECT COLUMN_NAME, DATA_TYPE FROM {table[0].upper()}.INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{table[1].upper()}' AND TABLE_NAME = '{table[2].upper()}'
        """, show_spinner=False,
    )
    
    # Processing columns data
    columns_info = ""
    if isinstance(columns_query_result, list):
        for row in columns_query_result:
            column_name = row.get('COLUMN_NAME', 'N/A')
            data_type = row.get('DATA_TYPE', 'N/A')
            columns_info += f"- **{column_name}**: {data_type}\n"

    context = f"""
Here is the table name <tableName> {'.'.join(table)} </tableName>

<tableDescription>{table_description}</tableDescription>

Here are the columns of the {'.'.join(table)}

<columns>\n\n{columns_info}\n\n</columns>
    """

    # Handling metadata query
    if metadata_query:
        metadata_query_result = conn.query(metadata_query, show_spinner=False)
        metadata_info = ""

        if isinstance(metadata_query_result, list):
            for row in metadata_query_result:
                for key, value in row.items():
                    metadata_info += f"- **{key}**: {value}\n"

        context += f"\n\nAvailable metrics by COLUMN_NAME:\n\n{metadata_info}"

    return context

def get_system_prompt(dataset_choice):
    if dataset_choice == 'Regional University Enrollment Data':
        # For dataset_1, explicitly list the column names
        column_names = "The columns in this table are UNIVERSITY_NAME, UNIVERSITY_STATE, REGIONAL_CENTER_STATE, REGIONAL_CENTER_DISTRICT, LEVEL, TOTAL_MALE_ENROLLMENT, TOTAL_FEMALE_ENROLLMENT, TOTAL_ENROLLMENT."
        example_questions = """
        Example questions for this dataset:
        - "What is the total male and female enrollment at a specific university?" For UNIVERSITY_NAME, use a LIKE query to handle variations.
        - "Which universities in a particular state have the highest total male enrollment?" For UNIVERSITY_STATE, use a LIKE query for partial matches.
        - "Can you display details of total enrollments by gender for Acharya Nagarjuna University who is a PG Diploma?" This should use TOTAL_MALE_ENROLLMENT and TOTAL_FEMALE_ENROLLMENT columns.
        """
        table_context = get_table_context(
            table_name=QUALIFIED_TABLE_NAME_1,
            table_description=TABLE_DESCRIPTION_1,
            metadata_query=METADATA_QUERY_1
        )
    else:
        # For dataset_2, explicitly list the column names
        column_names = "The columns in this table are SCHOOL_NAME, GEOM, LATITUDE, LONGITUDE, SUBURB, STATE, POSTCODE, SECTOR, STATUS, GEOLOCATION, PARENT_SCHOOL_ID."
        example_questions = """
        Example questions for this dataset:
        - "List all schools located in a specific suburb." Use LIKE for SUBURB.
        - "Show the names and geographical coordinates of schools in a particular state." Use LIKE queries for CITY and STATE.
        - "How many schools are there in each sector (Government or Non-Government)?" Use SECTOR directly in your query.
        """
        table_context = get_table_context(
            table_name=QUALIFIED_TABLE_NAME_2,
            table_description=TABLE_DESCRIPTION_2,
            metadata_query=METADATA_QUERY_2
        )

    # Additional instruction for the AI to use specific columns
    ai_instruction = "When generating SQL queries, use only the columns listed above. Additionally, suggest graphical representations for the data when relevant, such as bar charts or line graphs. Don't change the column name using the 'AS' operator."
    return GEN_SQL.format(context=f"{table_context}\n{column_names}\n{example_questions}\n{ai_instruction}")

# do `streamlit run prompts.py` to view the initial system prompt in a Streamlit app
if __name__ == "__main__":
    st.header("EduRegion Explorer - Choose Your Dataset")
    dataset_choice = st.radio(
    "Select a dataset to analyze:",
    ('Regional University Enrollment Data', 'Australian Educational Institutions Insights')
    )
    st.markdown(get_system_prompt(dataset_choice))