import streamlit as st  # Python framework used for creating interactive data apps
import pandas as pd  # Python library: Makes it easy to work with tabular data
# plotly: python graphing library    plotly.express: Create common figures more easily
import plotly.express as px
import json  # To load mappings from JSON file
import os  # To check if files exist
import datetime  # for working with dates

# Streamlit page setup
st.set_page_config(page_title="My Finances", page_icon="💰", layout="wide")

# Where categories and mappings are stored
category_file = "category_mappings_example.json"


# Function to assign categories to each transaction
def categorize_transactions(df, categories):
    # Initialize all transactions as uncategorized
    df["Category"] = "Uncategorized"

    # Loop through each category and its keywords. The items() method returns all key-value pairs in a dictionary
    for category, keywords in categories.items():
        # if category is uncategorized or keywords is empty, go to next loop iteration
        if category == "Uncategorized" or not keywords:
            continue

        lowered_keywords = [keyword.lower().strip() for keyword in keywords]

        # If keyword exists in mapping, assign appropriate category
        for idx, row in df.iterrows():  # Loop through each row in DataFrame
            description = row["Description"].lower().strip()
            for keyword in lowered_keywords:
                if keyword in description:
                    df.at[idx, "Category"] = category
                    break

    return df


# Load transactions from file into pandas dataframe, and call categorize_transactions
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
    st.title("My Finance Dashboard")
    st.markdown("**Past 12 Months**")

    # Check if json file exists. If it does, open it and load into Python dictionary called 'categories'
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
            # =================================================
            # Set up to get only last 12 months of data
            # =================================================
            today = datetime.date.today()
            first_day_this_month = today.replace(day=1)

            # Convert date to pandas Timestamp
            first_day_ts = pd.Timestamp(first_day_this_month)
            # Gives first day 12 months ago
            start_date_ts = first_day_ts - pd.DateOffset(months=11)
            start_date = start_date_ts.date()  # convert back to date

            end_date = today

            df_last12 = df[(df["Date"] >= start_date)
                           & (df["Date"] <= end_date)]

            # =================================================
            # Graph 1: Cumulative Net Change
            # =================================================
            df_sorted = df_last12.sort_values("Date")
            # pandas method - creates cumulative sum column
            df_sorted["Net Balance"] = df_sorted["Amount"].cumsum()

            # Create line chart using plotly express
            cnb_fig = px.line(df_sorted,
                              x="Date",
                              y="Net Balance",
                              title="Cumulative Net Change")

            # Format x axis
            cnb_fig.update_xaxes(
                dtick="M1",  # Tick at every month
                tickformat="%b %Y",
                ticklabelmode="period"  # Center labels in middle of month
            )

            # Add horizontal line at x-axis
            cnb_fig.add_hline(y=0, line_dash="solid", line_color="black")

            # Update y axis label
            cnb_fig.update_layout(yaxis_title="Balance ($)")

            # write to streamlit
            st.write(cnb_fig)

            # =================================================
            # Table 1: Monthly Summary
            # =================================================
            summary_df = df_last12.copy()

            # Create column with month/year objects for sorting
            summary_df["MonthPeriod"] = pd.to_datetime(
                summary_df["Date"]).dt.to_period("M")

            # Create month column for display
            summary_df["Month"] = summary_df["MonthPeriod"].dt.strftime(
                "%b %Y")

            # Calculate credits and debits values for each month (will be stored as a pandas series where index=MonthPeriod, value=sum of amounts)
            credits = summary_df[summary_df["Amount"] > 0].groupby("MonthPeriod")[
                "Amount"].sum()
            debits = summary_df[summary_df["Amount"] < 0].groupby("MonthPeriod")[
                "Amount"].sum().abs()

            # Combine credits and debits into a dataframe, index is MonthPeriod
            monthly_sum = pd.DataFrame({
                "Credits": credits,
                "Debits": debits
            })

            # Sort with most recent month at top
            monthly_sum = monthly_sum.sort_values(
                "MonthPeriod", ascending=False)

            # Calculate Net Change
            monthly_sum["Net Change"] = monthly_sum["Credits"] - \
                monthly_sum["Debits"]

            # Add Month column for display
            monthly_sum["Month"] = monthly_sum.index.strftime("%b %Y")

            # Move month to front
            monthly_sum = monthly_sum[["Month",
                                      "Credits", "Debits", "Net Change"]]

            # Reset index to get rid of MonthPeriod
            monthly_sum = monthly_sum.reset_index(drop=True)

            # function to color net change red=negative green=positive
            def color_net_change(value):
                # Return string will become inline css for coloring
                return f"color: {'green' if value > 0 else 'red'};"

            # Display table in streamlit
            st.subheader("Monthly Summary")
            # Write table to streamlit
            # applymap() - apply a function element-wise to a DataFrame (or subset of DataFrame)
            # format() - Change all values in subset to have 2 decimal places
            st.write(monthly_sum.style
                     .applymap(color_net_change, subset=["Net Change"])
                     .format("{:.2f}", subset=["Credits", "Debits", "Net Change"])
                     )

            # =================================================
            # Chart 1: Spending by Category
            # =================================================
            # group dataframe by category
            pie_df = df_last12[df_last12["Amount"] < 0]
            pie_df = pie_df.groupby("Category")[
                "Amount"].sum().abs().reset_index()

            pie_fig = px.pie(
                pie_df,
                values="Amount",
                names="Category",
                title="Spending by Category"
            )
            st.write(pie_fig)

            # =================================================
            # Table 2: Top Vendors
            # =================================================
            vendor_df = df_last12.copy()

            vendor_df = vendor_df[vendor_df["Amount"] < 0]

            # Group by vendor and sum total spending - returns a pandas series
            vendor_sum = vendor_df.groupby("Description")["Amount"].sum().abs()

            # Convert series to DataFrame
            vendor_df = pd.DataFrame({
                "Amount": vendor_sum
            })

            vendor_df = vendor_df.sort_values(
                by='Amount', ascending=False).reset_index()

            st.subheader("Top Vendors")
            st.write(vendor_df.style
                     .format("{:.2f}", subset=["Amount"]))

            # =================================================
            # Table 3: Credits and Debits tabs
            # =================================================
            debits_df = df_last12[df_last12["Amount"] < 0]
            credits_df = df_last12[df_last12["Amount"] >= 0]

            st.subheader("All Transactions")

            tab1, tab2 = st.tabs(["Credits", "Debits"])
            with tab1:
                st.write(credits_df.style
                         .format("{:.2f}", subset=["Amount"]))
            with tab2:
                st.write(debits_df.style
                         .format("{:.2f}", subset=["Amount"]))


main()
