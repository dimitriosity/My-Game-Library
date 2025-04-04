
import xml.etree.ElementTree as ET
import requests
import pandas as pd
import streamlit as st
import time

# --- SETTINGS ---
COLLECTION_XML_FILE = "collection.xml"
BGG_API_DELAY = 1.5

# --- LOAD XML ---
tree = ET.parse(COLLECTION_XML_FILE)
root = tree.getroot()

# --- EXTRACT BASIC INFO ---
games = []
for item in root.findall("item"):
    game_id = item.attrib.get("objectid")
    title = item.find("name").text if item.find("name") is not None else "Unknown"
    image_url = item.find("image").text if item.find("image") is not None else ""
    games.append({"Game ID": game_id, "Title": title, "Image URL": image_url})

# --- FETCH DETAILS FROM BGG API ---
def fetch_game_details(game_id):
    url = f"https://boardgamegeek.com/xmlapi2/thing?id={game_id}&stats=1"
    response = requests.get(url)
    root = ET.fromstring(response.content)
    item = root.find("item")

    year = item.find("yearpublished").attrib.get("value", "") if item.find("yearpublished") is not None else ""
    avg = item.find("./statistics/ratings/average").attrib.get("value", "") if item.find("./statistics/ratings/average") is not None else ""
    rank_elem = item.find("./statistics/ratings/ranks/rank[@name='boardgame']")
    rank = rank_elem.attrib.get("value", "Not Ranked") if rank_elem is not None else "Not Ranked"

    return year, avg, rank

@st.cache_data
def load_full_data():
    detailed = []
    for i, game in enumerate(games):
        year, avg, rank = fetch_game_details(game["Game ID"])
        game["Year Published"] = year
        game["Average Rating"] = avg
        game["BGG Rank"] = rank
        detailed.append(game)
        time.sleep(BGG_API_DELAY)
    return pd.DataFrame(detailed)

# --- STREAMLIT DASHBOARD ---
st.title("🎲 My Board Game Collection")
st.markdown("This dashboard displays your owned board games from BoardGameGeek.")

with st.spinner("Loading game details from BGG..."):
    df = load_full_data()

# Filter/Search
search = st.text_input("Search by title")
filtered_df = df[df["Title"].str.contains(search, case=False)] if search else df

# Sort Option
sort_by = st.selectbox("Sort by", ["Title", "Year Published", "Average Rating", "BGG Rank"])
filtered_df = filtered_df.sort_values(by=sort_by)

# Display as Gallery
grid_cols = st.slider("Cards per row", 2, 6, 4)

for i in range(0, len(filtered_df), grid_cols):
    cols = st.columns(grid_cols)
    for col, (_, row) in zip(cols, filtered_df.iloc[i:i+grid_cols].iterrows()):
        col.image(row["Image URL"], caption=f"{row['Title']}\n📅 {row['Year Published']}  ⭐ {row['Average Rating']}  🏆 {row['BGG Rank']}", use_column_width=True)
