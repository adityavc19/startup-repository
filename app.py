import streamlit as st
import sqlite3
import pandas as pd

DB_NAME = "startups.db"
TABLE_NAME = "startups"

st.set_page_config(page_title="Startup Repository", layout="wide")

# Custom CSS for premium white background and colored sections
st.markdown("""
<style>
    /* Gradient text for main title */
    h1 {
        background: linear-gradient(90deg, #4F46E5, #9333EA);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
        padding-bottom: 0.2rem;
    }
    
    /* Subtle background for the metric containers */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #EEF2FF 0%, #F5F3FF 100%);
        border: 1px solid #E0E7FF;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    
    /* Make metric values pop */
    [data-testid="stMetricValue"] {
        color: #4F46E5 !important;
        font-weight: 800 !important;
    }
    
    /* Expander card styling */
    [data-testid="stExpander"] {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        margin-bottom: 0.5rem;
    }
    
    /* Colored section highlight for the subheaders */
    h2, h3 {
        color: #1E293B !important;
        border-left: 4px solid #4F46E5;
        padding-left: 10px;
        margin-top: 1.5rem !important;
    }
</style>
""", unsafe_allow_html=True)

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

# --- Pre-process Data ---
df['date'] = pd.to_datetime(df['date'], errors='coerce')

# --- Last Updated Section ---
max_date = df['date'].max()
if pd.notna(max_date):
    recent_sources = df[df['date'] == max_date]['source'].dropna().unique()
    sources_str = ", ".join(sorted(str(s) for s in recent_sources))
    st.info(f"📅 **Last Updated:** {max_date.strftime('%b %d, %Y')} &nbsp;&nbsp;|&nbsp;&nbsp; 📰 **Recent Sources:** {sources_str}")

# --- Tabs ---
tab_all, tab_consumer = st.tabs(["📊 All Startups", "🎯 Consumer Spotlight"])

# ========================================
# TAB 1: ALL STARTUPS (existing view)
# ========================================
with tab_all:
    # --- Filters ---
    st.subheader("Filter Data")
    f_col1, f_col2, f_col3, f_col4 = st.columns(4)

    with f_col1:
        search_term = st.text_input("Search Company", "", key="search_all")

    with f_col2:
        sectors = ["All"] + sorted([str(s) for s in df['sector'].dropna().unique()])
        selected_sector = st.selectbox("Category", sectors, key="sector_all")

    with f_col3:
        sources = ["All"] + sorted([str(s) for s in df['source'].dropna().unique()])
        selected_source = st.selectbox("Source", sources, key="source_all")

    with f_col4:
        countries = ["All"] + sorted([str(c) for c in df['country'].dropna().unique() if c != 'Unknown']) + ["Unknown"]
        selected_country = st.selectbox("Country", countries, key="country_all")

    f_col5, _ = st.columns(2)
    with f_col5:
        min_date = df['date'].min().date() if not df['date'].dropna().empty else pd.Timestamp('2000-01-01').date()
        max_date_val = df['date'].max().date() if not df['date'].dropna().empty else pd.Timestamp('today').date()
        date_range = st.date_input("Date Range", value=(min_date, max_date_val), key="date_all")

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

    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start_date, end_date = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
        filtered_df = filtered_df[
            (filtered_df['date'] >= start_date) & (filtered_df['date'] <= end_date)
        ]

    # --- Display Stats ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Startups", len(filtered_df))
    with col2:
        st.metric("Unique Sectors", filtered_df['sector'].nunique())
    with col3:
        st.metric("Total Sources", filtered_df['source'].nunique())

    # --- Display Data ---
    # Sort by date descending
    filtered_df = filtered_df.sort_values('date', ascending=False, na_position='last')

    st.subheader("Data Table")
    st.dataframe(
        filtered_df,
        use_container_width=True,
        height=800,
        column_config={
            "company": st.column_config.TextColumn("Company"),
            "sector": st.column_config.TextColumn("Category"),
            "tags": st.column_config.TextColumn("Specific Tags"),
            "description": st.column_config.TextColumn("Description"),
            "amount": st.column_config.TextColumn("Amount Raised"),
            "date": st.column_config.DateColumn("Date of Funding"),
            "country": st.column_config.TextColumn("Country"),
            "source": st.column_config.TextColumn("Source"),
        },
        hide_index=True
    )


# ========================================
# TAB 2: CONSUMER SPOTLIGHT
# ========================================
with tab_consumer:
    st.subheader("🎯 Interesting Consumer Startups")
    st.markdown("Curated view of consumer-facing startups — apps, brands, social, gaming, wellness, and more.")

    # Define consumer categories
    consumer_sectors = [
        "Consumer & Social", "Media & Gaming", "E-Commerce & Retail",
        "E-commerce & Retail", "Education", "Agtech / Foodtech",
        "Food Tech", "Agtech",
    ]
    consumer_sector_keywords = [
        "SOCIAL", "GAMES", "GAMING", "FITNESS", "DATING", "CREATIVE",
        "EDTECH", "MEDIA", "ANIMATION", "MARKETPLACE",
    ]
    consumer_tag_keywords = [
        "consumer", "social", "gaming", "wellness", "fitness",
        "food", "beauty", "fashion", "travel", "entertainment",
        "music", "sports", "lifestyle",
    ]
    consumer_desc_keywords = [
        "consumer", "wellness", "gaming", "social", "mobile app",
        "beauty", "fashion", "food", "travel", "entertainment",
        "lifestyle", "fitness", "dating", "music", "sports", "beer",
        "diaper", "jewelry", "greeting card", "pet", "kids",
        "personal", "wearable",
    ]

    # Build consumer filter
    df_consumer = df.copy()
    df_consumer['date'] = pd.to_datetime(df_consumer['date'], errors='coerce')

    is_consumer_sector = df_consumer['sector'].isin(consumer_sectors)
    is_consumer_sector_kw = df_consumer['sector'].apply(
        lambda x: any(kw in str(x).upper() for kw in consumer_sector_keywords) if pd.notna(x) else False
    )
    is_consumer_tag = df_consumer['tags'].apply(
        lambda x: any(kw in str(x).lower() for kw in consumer_tag_keywords) if pd.notna(x) else False
    )
    is_consumer_desc = df_consumer['description'].apply(
        lambda x: any(kw in str(x).lower() for kw in consumer_desc_keywords) if pd.notna(x) else False
    )

    df_consumer = df_consumer[is_consumer_sector | is_consumer_sector_kw | is_consumer_tag | is_consumer_desc]

    # --- Consumer Filters ---
    cf_col1, cf_col2, cf_col3 = st.columns(3)

    with cf_col1:
        consumer_search = st.text_input("Search Consumer Startups", "", key="search_consumer")

    with cf_col2:
        consumer_categories = ["All"] + sorted(df_consumer['sector'].dropna().unique().tolist())
        selected_consumer_cat = st.selectbox("Category", consumer_categories, key="cat_consumer")

    with cf_col3:
        consumer_countries = ["All"] + sorted([
            str(c) for c in df_consumer['country'].dropna().unique() if c != 'Unknown'
        ]) + ["Unknown"]
        selected_consumer_country = st.selectbox("Country", consumer_countries, key="country_consumer")

    # Apply consumer filters
    if consumer_search:
        df_consumer = df_consumer[
            df_consumer['company'].str.contains(consumer_search, case=False, na=False) |
            df_consumer['description'].str.contains(consumer_search, case=False, na=False)
        ]

    if selected_consumer_cat != "All":
        df_consumer = df_consumer[df_consumer['sector'] == selected_consumer_cat]

    if selected_consumer_country != "All":
        df_consumer = df_consumer[df_consumer['country'] == selected_consumer_country]

    # --- Consumer Stats ---
    cc1, cc2, cc3, cc4 = st.columns(4)
    with cc1:
        st.metric("Consumer Startups", len(df_consumer))
    with cc2:
        # Count those with known funding
        funded = df_consumer[~df_consumer['amount'].isin(["Unknown", "Undisclosed", "nan", ""])]
        st.metric("With Known Funding", len(funded))
    with cc3:
        st.metric("Categories", df_consumer['sector'].nunique())
    with cc4:
        st.metric("Countries", df_consumer['country'].nunique())

    # --- Consumer Cards View ---
    st.markdown("---")

    # Sort by date (newest first), then show as cards
    df_consumer_sorted = df_consumer.sort_values('date', ascending=False, na_position='last')

    # Display as expandable cards
    for _, row in df_consumer_sorted.iterrows():
        company = row.get('company', 'Unknown')
        sector = row.get('sector', 'Unknown')
        description = row.get('description', 'Unknown')
        amount = row.get('amount', 'Unknown')
        location = row.get('location', 'Unknown')
        country = row.get('country', 'Unknown')
        date = row.get('date', '')
        source = row.get('source', 'Unknown')
        tags = row.get('tags', '')
        stage = row.get('stage', 'Unknown')
        website = str(row.get('website', '') or '')

        date_str = date.strftime('%b %d, %Y') if pd.notna(date) else 'N/A'

        # Funding badge color
        if amount not in ('Unknown', 'Undisclosed', 'nan', ''):
            amount_display = f"💰 {amount}"
        else:
            amount_display = "💰 Undisclosed"

        with st.expander(f"**{company}** — {amount_display}  |  {sector}  |  {date_str}"):
            info_col1, info_col2 = st.columns(2)
            with info_col1:
                st.markdown(f"**📝 Description:** {description}")
                st.markdown(f"**🏷️ Tags:** {tags}" if tags and tags != 'nan' else "")
                st.markdown(f"**📍 Location:** {location}")
            with info_col2:
                st.markdown(f"**🌍 Country:** {country}")
                st.markdown(f"**📈 Stage:** {stage}" if stage and stage != 'Unknown' else "")
                st.markdown(f"**📰 Source:** {source}")
                if website and website.strip():
                    st.markdown(f"**🔗 Website:** [{website}]({website})")

    # Also show as a table below
    st.markdown("---")
    st.subheader("Full Consumer Startups Table")
    st.dataframe(
        df_consumer_sorted,
        use_container_width=True,
        height=800,
        column_config={
            "company": st.column_config.TextColumn("Company"),
            "sector": st.column_config.TextColumn("Category"),
            "tags": st.column_config.TextColumn("Tags"),
            "description": st.column_config.TextColumn("Description"),
            "amount": st.column_config.TextColumn("Funding"),
            "date": st.column_config.DateColumn("Date"),
            "country": st.column_config.TextColumn("Country"),
            "source": st.column_config.TextColumn("Source"),
            "stage": st.column_config.TextColumn("Stage"),
            "website": st.column_config.LinkColumn("Website", display_text="Visit →"),
        },
        hide_index=True
    )

st.markdown("---")
st.caption("Built with Streamlit and SQLite")
