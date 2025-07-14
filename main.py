import streamlit as st  # Python framework used for creating interactive data apps
import pandas as pd  # Python library: Makes it easy to work with tabular data
# plotly: python graphing library    plotly.express: Create common figures more easily
import plotly.express as px
import json  # To load mappings from JSON file
import os  # To check if files exist
import datetime  # for working with dates

# Streamlit page setup
st.set_page_config(page_title="Joey's Finances", page_icon="💰", layout="wide")

# Where categories and mappings are stored
category_file = "category_mappings.json"


# Function to assign categories to each transcation row
def categorize_transactions(df, categories):
    df["Category"] = "Uncategorized"  # Initialize all rows as uncategorized

    # Loop through each category and its keywords. The items() method returns all key-value pairs in a dictionary
    for category, keywords in categories.items():
        # if category is uncategorized or keywords is empty, go to next loop iteration
        if category == "Uncategorized" or not keywords:
            continue

        lowered_keywords = [keyword.lower().strip() for keyword in keywords]

        for idx, row in df.iterrows():  # Loop through each row in DataFrame
            description = row["Description"].lower().strip()
            for keyword in lowered_keywords:
                if keyword in description:
                    df.at[idx, "Category"] = category
                    break

    return df


def load_transactions(file, categories):
    try:
        df = pd.read_csv(file)

        # Clean up data
        df.columns = [col.strip() for col in df.columns]
        df["Date"] = pd.to_datetime(df["Date"], format="%m/%d/%Y")
        df["Date"] = df["Date"].dt.date

        return categorize_transactions(df, categories)
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return None


def main():
    st.title("Joey's Finance Dashboard")

    # Then, check if category is already mapped, and update it
    if os.path.exists(category_file):
        with open(category_file, "r") as f:
            categories = json.load(f)
    else:
        categories = {"Uncategorized": []}

    # Display a file uploader widget
    uploaded_file = st.file_uploader(
        "Upload your transaction CSV file in the format: [Date],[Description],[Amount]", type=["csv"])

    if uploaded_file is not None:
        # df stands for DataFrame. Primary data structure in pandas that you can filter, group, sort, summarize, etc. Like an Excel table
        df = load_transactions(uploaded_file, categories)

        if df is not None:
            today = datetime.date.today()
            first_day_this_month = today.replace(day=1)

            first_day_ts = pd.Timestamp(first_day_this_month)
            start_date_ts = first_day_ts - pd.DateOffset(months=11)
            start_date = start_date_ts.date()

            end_date = today

            df_last12 = df[(df["Date"] >= start_date)
                           & (df["Date"] <= end_date)]

            # Table 1: Credits and Debits tabs
            debits_df = df_last12[df_last12["Amount"] < 0].copy()
            credits_df = df_last12[df_last12["Amount"] >= 0].copy()

            tab1, tab2 = st.tabs(["Debits", "Credits"])
            with tab1:
                st.write(debits_df)
            with tab2:
                st.write(credits_df)


main()
