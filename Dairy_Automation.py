import os
import json
import streamlit as st
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, select
from sqlalchemy.dialects.sqlite import JSON
from streamlit_option_menu import option_menu
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from fpdf import FPDF
import pandas as pd
import base64
from io import BytesIO
from PIL import Image
import pyodbc
import plotly.express as px
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from bidi.algorithm import get_display
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
import re

# Register Urdu font
# pdfmetrics.registerFont(TTFont("NotoNastaliqUrdu", "./ttf/NotoNastaliqUrdu-Regular.ttf"))
# ... (Previous imports remain the same)

# Database credentials (Update if needed)
SERVER = 'DESKTOP-SEH424V\\SQL'
DATABASE = 'Dairy_Automation'  # Updated database name
USERNAME = 'sa'
PASSWORD = 'Pakistan123!'

# Function to connect to the database
def get_connection():
    return pyodbc.connect(
        Driver='{ODBC Driver 17 for SQL Server}',
        Server=SERVER,
        Database=DATABASE,
        UID=USERNAME,
        PWD=PASSWORD
    )

# Initialize session states
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "add_record" not in st.session_state:
    st.session_state.add_record = False
if "show_records" not in st.session_state:
    st.session_state.show_records = False




# Custom CSS for a sticky footer
def apply_custom_css():
    st.markdown(
        """
        <style>
            .main .block-container {
                padding: 0 !important;
                margin: 0 auto !important;
                max-width: 80% !important;
            }
            .css-1d391kg, .css-1d391kg * {
                padding: 0 !important;
                margin: 0 !important;
                width: 80% !important;
            }
            .css-1v3fvcr {
                flex: 1;
                display: flex;
                flex-direction: column;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

apply_custom_css()

# Check login state
if not st.session_state.get("logged_in", False):
    # Streamlit app title
    st.markdown(
        """
        <h1 style="text-align: center;">Dairy Automation</h1>
        """,
        unsafe_allow_html=True
    )

st.markdown(
    """
    <style>
        .css-1d391kg {width: 80% !important;}
        .css-1v3fvcr {align-items: stretch !important;}
    </style>
    """,
    unsafe_allow_html=True
)



def update_database(updated_df):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        for index, row in updated_df.iterrows():
            query = """
                UPDATE [dbo].[tbl_dairy_daily_Milk]
                SET Daily_Milk = ?
                WHERE Date_Milk = ? AND Customers_ID = (
                    SELECT ID FROM [dbo].[tbl_dairy_Customers] WHERE Name = ?
                )
            """
            cursor.execute(query, (row['Total_Milk'], row['Date_Milk'], row['Name']))
        conn.commit()
        st.success("Database updated successfully!")
    except Exception as e:
        st.error(f"Error updating database: {e}")
    finally:
        conn.close()

selected = None
# Sidebar with option menu
with st.sidebar:
    if not st.session_state.logged_in:
        st.title("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if username == "admin" and password == "admin":  # Replace with actual authentication logic
                st.session_state.logged_in = True
                st.success("Logged in successfully!")
            else:
                st.error("Invalid username or password.")
    else:
        # Define selected only when logged in
        selected = option_menu(
            menu_title="Main Menu",
            options=["Dashboard", "Daily Milk Record", "Reporting", "Contact us", "Logout"],
            icons=["grid", "grid", "bar-chart", "phone", "box-arrow-right"],
            menu_icon="cast",
            default_index=0,
        )
# "grid", "file-earmark"

        if selected == "Logout":
            st.session_state.logged_in = False
            st.success("Logged out successfully!")

# Function to fetch all customers
def fetch_customers():
    try:
        conn = get_connection()
        query = """
            SELECT [ID], [Name], [Address], [Mobile_Number], [Email], [Rate]
            FROM [dbo].[tbl_dairy_Customers]
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error fetching customers: {e}")
        return pd.DataFrame()

# Function to insert daily milk record
# Function to insert daily milk record
def save_daily_milk_record(customer_id, milk_quantity, date):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Convert numpy types to native Python types
        customer_id = int(customer_id)
        milk_quantity = float(milk_quantity)

        query = """
            INSERT INTO [dbo].[tbl_dairy_daily_Milk] 
            ([Daily_Milk], [Date_Milk], [Customers_ID], [Created_Date], [Modifed_Date], [Deleted])
            VALUES (?, ?, ?, GETDATE(), GETDATE(), 0)
        """
        cursor.execute(query, (milk_quantity, date, customer_id))
        conn.commit()
        conn.close()
        st.success("Daily milk record saved successfully!")
    except Exception as e:
        st.error(f"Error saving daily milk record: {e}")


# Function to fetch all daily milk records
def fetch_daily_milk_records():
    try:
        conn = get_connection()
        query = """
            SELECT [ID], [Daily_Milk], [Date_Milk], [Customers_ID]
            FROM [dbo].[tbl_dairy_daily_Milk]
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error fetching daily milk records: {e}")
        return pd.DataFrame()

# Main logic for "Daily Milk Record"
# if selected == "Daily Milk Record" and st.session_state.logged_in:
#     st.subheader("Daily Milk Record")

#     # Fetch all customers
#     customers_df = fetch_customers()
#     if not customers_df.empty:
#         # Display customers in a dropdown
#         customer_names = customers_df["Name"].tolist()
#         selected_customer = st.selectbox("Select Customer", options=customer_names)

#         # Get the selected customer's ID
#         selected_customer_id = customers_df[customers_df["Name"] == selected_customer]["ID"].values[0]

#         # Text editor for milk quantity and date
#         milk_quantity = st.number_input("Milk Quantity (in liters)", min_value=0.0, step=0.1)
#         milk_date = st.date_input("Date")

#         if st.button("Save Milk Record"):
#             if milk_quantity > 0 and milk_date:
#                 save_daily_milk_record(selected_customer_id, milk_quantity, milk_date)
#             else:
#                 st.error("Please enter valid milk quantity and date.")

#         # Display all daily milk records
#         st.subheader("All Daily Milk Records")
#         milk_records_df = fetch_daily_milk_records()
#         if not milk_records_df.empty:
#             # Merge with customers table to get customer names
#             merged_df = pd.merge(milk_records_df, customers_df, left_on="Customers_ID", right_on="ID", how="left")
#             st.dataframe(merged_df[["Name", "Daily_Milk", "Date_Milk"]])
#         else:
#             st.info("No daily milk records found.")
#     else:
#         st.error("No customers found in the database. Please add customers first.")

def parse_milk_records(input_text):
    pattern = r"([\w\s]+)\s*:\s*([\d.]+)"
    matches = re.findall(pattern, input_text)
    return [(name.strip(), float(value)) for name, value in matches]

# Function to insert bulk daily milk records
def save_bulk_daily_milk_records(date, records, customers_df):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Convert customer names to a dictionary for quick lookup
        customer_dict = dict(zip(customers_df["Name"], customers_df["ID"]))

        inserted_count = 0
        for name, milk_quantity in records:
            if name in customer_dict:
                customer_id = int(customer_dict[name])

                query = """
                    INSERT INTO [dbo].[tbl_dairy_daily_Milk] 
                    ([Daily_Milk], [Date_Milk], [Customers_ID], [Created_Date], [Modifed_Date], [Deleted])
                    VALUES (?, ?, ?, GETDATE(), GETDATE(), 0)
                """
                cursor.execute(query, (milk_quantity, date, customer_id))
                inserted_count += 1
            else:
                st.warning(f"Customer '{name}' not found in the database.")

        conn.commit()

        # Query to calculate the sum of milk quantities for the current date, excluding "Shakeel Rajar" and "Shop"
        sum_query = """
            SELECT SUM([Daily_Milk]) AS Total_Milk
            FROM [dbo].[tbl_dairy_daily_Milk] dm
            JOIN [dbo].[tbl_dairy_Customers] c ON dm.[Customers_ID] = c.[ID]
            WHERE dm.[Date_Milk] = ?
            AND c.[Name] NOT IN ('Shakeel Rajar', 'Shop')
        """
        cursor.execute(sum_query, (date,))
        result = cursor.fetchone()
        total_milk = result[0] if result[0] is not None else 0

        conn.close()
        st.success(f"{inserted_count} daily milk records added successfully!")

        # Show the total milk quantity except for "Shakeel Rajar" and "Shop"
        st.info(f"Total milk quantity (excluding Shakeel Rajar and Shop) for {date}:     {total_milk}")

    except Exception as e:
        st.error(f"Error saving bulk daily milk records: {e}")

def generate_milk_report(month, year, rate_per_liter):
    try:
        conn = get_connection()
        query = """
            SELECT c.Name, 
                   SUM(dm.Daily_Milk) AS Total_Milk, 
                   SUM(dm.Daily_Milk) * ? AS Due_Payment
            FROM [dbo].[tbl_dairy_daily_Milk] dm
            JOIN [dbo].[tbl_dairy_Customers] c ON dm.Customers_ID = c.ID
            WHERE MONTH(dm.Date_Milk) = ? AND YEAR(dm.Date_Milk) = ?
            GROUP BY c.Name
            ORDER BY c.Name
        """
        df = pd.read_sql_query(query, conn, params=(rate_per_liter, month, year))
        conn.close()
        
        if df.empty:
            st.info("No records found for the selected month and year.")
        else:
            st.dataframe(df)
            
            total_milk = df['Total_Milk'].sum()
            total_due = df['Due_Payment'].sum()
            st.success(f"Total Milk for {month}/{year}: {total_milk} liters")
            st.success(f"Total Due Payment: {total_due} units")
    except Exception as e:
        st.error(f"Error generating report: {e}")
# name_mapping = {
#     "Sultan": "Sultan st 34",
#     "Shah sab": "Murtaza Shah st 26",
#     "Awais": "Awais Office",
#     "Parwaz sb": "Parwaz Sahab",
#     "Naveed": "Naveed st 29",
#     "Shakeel": "Shakeel Rajar",
#     "Shop": "Shop",
#     "Khokhar": "Khokhar Shop",
#     "Bashir sab": "Bashir NR Office",
#     "Zia indrive": "Zia Indrive",
#     "Mamu sabir": "Sabir Mamo",
#     "Habib office": "Habib DD Office",
#     "Home": "Sameeb Home",
#     "Naeem": "Naeem 30",
#     "Danial": "Danial Cousin",
#     "Extra": "Extra",
#     "Habib bhai": "Habib Bhai"
# }

# # Function to replace shared names with original names
# def update_names(data):
#     return [(name_mapping.get(key, key), value) for key, value in data]

# Main logic for bulk record entry
if selected == "Daily Milk Record" and st.session_state.logged_in:
    st.subheader("Bulk Daily Milk Record Entry")

    # Fetch all customers for validation
    customers_df = fetch_customers()

    milk_date = st.date_input("Date for Records")
    bulk_text = st.text_area("Paste Daily Milk Records (e.g., 'Shakeel : 70')")

    if st.button("Add Bulk Records"):
        if bulk_text and milk_date:
            parsed_records = parse_milk_records(bulk_text)
            if parsed_records:
                # updated_records = dict(update_names(parsed_records))  # Convert list of tuples back to a dictionary

                save_bulk_daily_milk_records(milk_date, parsed_records, customers_df)
            else:
                st.error("No valid records found. Please check the input format.")
        else:
            st.error("Please enter a valid date and paste records.")

    # Show current records
    st.subheader("Current Daily Milk Records")
    current_records = fetch_daily_milk_records()
    if not current_records.empty:
        merged_df = pd.merge(current_records, customers_df, left_on="Customers_ID", right_on="ID", how="left")
        st.dataframe(merged_df[["Name", "Daily_Milk", "Date_Milk"]])
    else:
        st.info("No records found.")

if selected == "Reporting" and st.session_state.logged_in:
    st.subheader("Milk Reporting")

    # Select date range
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date")
    with col2:
        end_date = st.date_input("End Date")

    if start_date and end_date:
        conn = get_connection()
        query = """
            SELECT c.Name, dm.Date_Milk, SUM(dm.Daily_Milk) AS Total_Milk, c.Rate
            FROM [dbo].[tbl_dairy_daily_Milk] dm
            JOIN [dbo].[tbl_dairy_Customers] c ON dm.Customers_ID = c.ID
            WHERE dm.Date_Milk BETWEEN ? AND ?
            GROUP BY c.Name, dm.Date_Milk, c.Rate
            ORDER BY dm.Date_Milk, c.Name
        """
        df = pd.read_sql_query(query, conn, params=(start_date, end_date))
        conn.close()

        if not df.empty:
            # Pivot table for better visualization
            pivot_df = df.pivot(index='Date_Milk', columns='Name', values='Total_Milk').fillna(0)
            pivot_df.reset_index(inplace=True)
            pivot_df.insert(0, 'Sr No', range(1, len(pivot_df) + 1))

            # Calculate total milk for each person
            sum_df = pivot_df.iloc[:, 2:].sum().to_frame().T
            sum_df.index = ['Total']
            sum_df.insert(0, 'Sr No', '')
            sum_df.insert(1, 'Date_Milk', '')

            final_df = pd.concat([sum_df, pivot_df], ignore_index=True)

            # Display milk records in a table
            st.subheader("Milk Records Table")
            AgGrid(final_df)

            # Group by customer to get total milk and rate
            total_milk_by_customer = df.groupby(['Name', 'Rate'])['Total_Milk'].sum().reset_index()
            total_milk_by_customer['Total_Amount'] = total_milk_by_customer['Total_Milk'] * total_milk_by_customer['Rate']

            # Show a bar chart of total milk consumption
            st.subheader("Total Milk Consumption by Customer")
            fig1 = px.bar(
                total_milk_by_customer, x="Name", y="Total_Milk", 
                title="Total Milk Consumed by Customer",
                labels={"Total_Milk": "Total Milk Consumed", "Name": "Customer Name"},
                text="Total_Milk",
                color="Name",
                color_discrete_sequence=px.colors.qualitative.Plotly
            )

            # Add rate as annotation in hover tooltips
            fig1.update_traces(
                hovertemplate="<b>%{x}</b><br>Total Milk: %{y}L<br>Rate: Rs. %{customdata}/L",
                customdata=total_milk_by_customer['Rate']
            )

            fig1.update_layout(template="plotly_white", hovermode="x unified")
            st.plotly_chart(fig1)

            # Select customer for detailed view
            st.subheader("Daily Milk Consumption for Selected Customer")
            selected_customer = st.selectbox("Select a Customer", total_milk_by_customer['Name'])

            # Filter data for selected customer
            customer_data = total_milk_by_customer[total_milk_by_customer['Name'] == selected_customer]
            customer_rate = customer_data.iloc[0]['Rate']
            customer_total_milk = customer_data.iloc[0]['Total_Milk']
            customer_total_amount = customer_data.iloc[0]['Total_Amount']

            # Display customer's rate and total amount
            st.info(f"**Rate for {selected_customer}: Rs.{customer_rate}/L**")
            st.success(f"**Total Amount Due: Rs.{customer_total_amount:.2f}** (Total Milk: {customer_total_milk}L × Rate: Rs.{customer_rate}/L)")

            # Show daily milk consumption for selected customer
            daily_usage = df[df['Name'] == selected_customer]
            fig2 = px.bar(
                daily_usage, x="Date_Milk", y="Total_Milk", 
                title=f"Daily Milk Consumption for {selected_customer}",
                labels={"Total_Milk": "Milk Consumed", "Date_Milk": "Date"},
                text="Total_Milk",
                color="Date_Milk",
                color_discrete_sequence=px.colors.qualitative.Plotly
            )

            fig2.update_layout(template="plotly_white", hovermode="x unified")
            st.plotly_chart(fig2)

            # Export report to Excel
            def convert_df_to_excel(df):
                output = BytesIO()
                with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                    df.to_excel(writer, sheet_name="Milk Report", index=False)
                processed_data = output.getvalue()
                return processed_data

            st.download_button(
                label="Download Excel Report",
                data=convert_df_to_excel(final_df),
                file_name="Milk_Report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("No data found for the selected date range.")
