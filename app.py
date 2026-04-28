import streamlit as st
import sqlite3
import pandas as pd

DB_NAME = "startups.db"
TABLE_NAME = "startups"

st.set_page_config(page_title="Startup Repository", layout="wide")

st.title("🚀 Startup Repository")
st.markdown("A unified database for tracking startups, their sectors, and funding.")

def load_data():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql(f"SELECT * FROM {TABLE_NAME}", conn)
    conn.close()
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Failed to load data from database. Did you run the ingestion script? Error: {e}")
    st.stop()

# --- Filters ---
st.sidebar.header("Filters")

# Search by company name
search_term = st.sidebar.text_input("Search Company", "")

# Sector Filter
sectors = ["All"] + sorted([str(s) for s in df['sector'].dropna().unique()])
selected_sector = st.sidebar.selectbox("Sector", sectors)

# Source Filter
sources = ["All"] + sorted([str(s) for s in df['source'].dropna().unique()])
selected_source = st.sidebar.selectbox("Source", sources)

# Country Filter
countries = ["All"] + sorted([str(c) for c in df['country'].dropna().unique() if c != 'Unknown']) + ["Unknown"]
selected_country = st.sidebar.selectbox("Country", countries)

# --- Apply Filters ---
filtered_df = df.copy()

if search_term:
    filtered_df = filtered_df[filtered_df['company'].str.contains(search_term, case=False, na=False)]

if selected_sector != "All":
    filtered_df = filtered_df[filtered_df['sector'] == selected_sector]

if selected_source != "All":
    filtered_df = filtered_df[filtered_df['source'] == selected_source]

if selected_country != "All":
    filtered_df = filtered_df[filtered_df['country'] == selected_country]

# --- Display Stats ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Startups", len(filtered_df))
with col2:
    st.metric("Unique Sectors", filtered_df['sector'].nunique())
with col3:
    st.metric("Total Sources", filtered_df['source'].nunique())

# --- Display Data ---
st.subheader("Data Table")
st.dataframe(
    filtered_df,
    use_container_width=True,
    column_config={
        "company": st.column_config.TextColumn("Company"),
        "sector": st.column_config.TextColumn("Sector"),
        "description": st.column_config.TextColumn("Description"),
        "amount": st.column_config.TextColumn("Amount Raised"),
        "date": st.column_config.DateColumn("Date of Funding"),
        "country": st.column_config.TextColumn("Country"),
        "source": st.column_config.TextColumn("Source"),
    },
    hide_index=True
)

st.markdown("---")
st.caption("Built with Streamlit and SQLite")
