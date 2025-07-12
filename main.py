import streamlit as st  # Turn Python scripts into interactive web apps
import pandas as pd  # Makes it easy to work with data
import plotly.express as px  # Create good looking interactive charts quickly
import json  # To load mappings from JSON file
import os  # To handle file paths or check files

# Streamlit setup
st.set_page_config(page_title="Joey's Finances", page_icon="💰", layout="wide")

category_file = "category_mappings.json"

# Set default category to uncategorized
if "categories" not in st.session_state:
    st.session_state.categories = {
        "Uncategorized": []
    }

# Then, check if category is already mapped, and update it
if os.path.exists(category_file):
    with open(category_file, "r") as f:
        st.session_state.categories = json.load(f)


def save_categories():
    with open(category_file, "w") as f:
        json.dump(st.session_state.categories, f)


def categorize_transcations(df):
    df["Category"] = "Uncategorized"

    for category, keywords in st.session_state.categories.items():  # Loop through all categories
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


def load_transactions(file):
    try:
        df = pd.read_csv(file)

        # Cleam up data
        df.columns = [col.strip() for col in df.columns]
        df["Date"] = pd.to_datetime(df["Date"], format="%m/%d/%Y")
        df["Date"] = df["Date"].dt.date

        return categorize_transcations(df)
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return None


def main():
    st.title("Joey's Finance Dashboard")

    # Dsiplay a file uploader widget
    uploaded_file = st.file_uploader(
        "Upload your transaction CSV file in the format: [Date],[Description],[Amount]", type=["csv"])

    if uploaded_file is not None:
        # df stands for DataFrame. Primary data structure in pandas that you can filter, group, sort, summarize, etc. Like an Excel table
        df = load_transactions(uploaded_file)

        if df is not None:
            # Table 1: Credits and Debits tabs
            debits_df = df[df["Amount"] < 0].copy()
            credits_df = df[df["Amount"] >= 0].copy()

            tab1, tab2 = st.tabs(["Debits", "Credits"])
            with tab1:
                st.write(debits_df)
            with tab2:
                st.write(credits_df)


main()
