import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
import random
import time
from datetime import datetime

# Page setup
st.set_page_config(page_title="The Dragon's Sanctuary", page_icon="🐉")

# --- Whimsical Fairy Background, Berry-Pink Text & Falling Petals ---
st.markdown("""
<style>
.stApp {
    background: linear-gradient(180deg, #FFE4EC 0%, #FFB6C1 48%, #E1BEE7 100%);
    background-attachment: fixed;
}
.stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp label, .stApp span, .stApp div {
    color: #9C1B5B !important;
}
[data-testid="stExpander"] {
    background-color: rgba(255, 255, 255, 0.85);
    border: 1.5px solid #FF69B4;
    border-radius: 18px;
    box-shadow: 0 4px 15px rgba(255, 105, 180, 0.15);
}
.stButton > button {
    border-radius: 20px;
    border: 1px solid #FF69B4;
    background-color: #FFF5F8;
    color: #9C1B5B !important;
    transition: all 0.2s ease;
}
.stButton > button:hover, .stButton > button:hover * {
    background-color: #FF69B4;
    color: white !important;
    box-shadow: 0 0 12px rgba(255, 105, 180, 0.45);
}
[data-testid="stAlert"] {
    background-color: rgba(255, 240, 245, 0.85) !important;
    border: 1px solid #FFB6C1 !important;
    border-radius: 15px !important;
}
[data-testid="stAlert"] p {
    color: #E75480 !important;
}
@keyframes floatDown {
    0% { transform: translateY(-10vh) rotate(0deg); opacity: 0; }
    15% { opacity: 0.85; }
    85% { opacity: 0.85; }
    100% { transform: translateY(105vh) rotate(360deg); opacity: 0; }
}
.petal {
    position: fixed;
    top: -5vh;
    font-size: 20px;
    pointer-events: none;
    z-index: 0;
    animation: floatDown linear infinite;
}
</style>
<div class="petal" style="left: 8%; animation-duration: 11s; animation-delay: 0s;">🌸</div>
<div class="petal" style="left: 24%; animation-duration: 14s; animation-delay: 3s;">✨</div>
<div class="petal" style="left: 42%; animation-duration: 12s; animation-delay: 1.5s;">🌸</div>
<div class="petal" style="left: 65%; animation-duration: 15s; animation-delay: 4s;">🌷</div>
<div class="petal" style="left: 82%; animation-duration: 10s; animation-delay: 2s;">✨</div>
<div class="petal" style="left: 93%; animation-duration: 13s; animation-delay: 5s;">🌸</div>
""", unsafe_allow_html=True)

# Time-of-day greeting
hour = datetime.now().hour
if hour < 12:
    greeting = "☀️ Good morning! Ready for a cozy reading day?"
elif hour < 18:
    greeting = "🌸 Happy afternoon! Welcome back to your book hoard."
else:
    greeting = "🌙 Cozy evening reading session?"

st.title("🐉 The Dragon's Sanctuary 🌸")
st.caption(greeting)

# Detect which NFC door she tapped (?door=willow vs ?door=books)
door = st.query_params.get("door", "books")
if door == "willow":
    st.info("🌸 You tapped the Willow Tree Stand! Check **💌 Dragon's Whimsy** for notes & your dragon.")

# Connect to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
COLUMNS = ["Title", "Author", "Shelf", "Rating", "Notes", "CoverURL"]
SHELVES = ["Books I Own", "Books I Want to Read", "Books I've Read"]

df = conn.read(worksheet="Sheet1", ttl=0)
if df.empty or list(df.columns) != COLUMNS:
    df = pd.DataFrame(columns=COLUMNS)
else:
    df = df.dropna(how="all")

def save_books(updated_df):
    conn.update(worksheet="Sheet1", data=updated_df)

def fetch_book_cover(title, author):
    query = f"{title} {author}".strip()
    encoded_q = requests.utils.quote(query)
    headers = {"User-Agent": "Mozilla/5.0 (DragonsSanctuaryBookTracker)"}
    try:
        ol_url = f"https://openlibrary.org{encoded_q}&limit=1"
        ol_res = requests.get(ol_url, headers=headers, timeout=8).json()
        docs = ol_res.get("docs", [])
        if docs:
            first_doc = next(iter(docs))
            cover_id = first_doc.get("cover_i")
            if cover_id:
                return f"https://openlibrary.org{cover_id}-L.jpg"
    except Exception:
        pass
    try:
        gb_url = f"https://googleapis.com{encoded_q}&maxResults=1"
        gb_res = requests.get(gb_url, headers=headers, timeout=8).json()
        items = gb_res.get("items", [])
        if items:
            first_item = next(iter(items))
            links = first_item.get("volumeInfo", {}).get("imageLinks", {})
            thumb = links.get("thumbnail") or links.get("smallThumbnail")
            if thumb:
                return thumb.replace("http://", "https://")
    except Exception:
        pass
    return ""

# --- Hoard Stats & Reading Goal Bar ---
try:
    goal_df = conn.read(worksheet="DragonStats", ttl=0)
    reading_goal = int(goal_df.at[0, "Goal"]) if "Goal" in goal_df.columns and pd.notna(goal_df.at[0, "Goal"]) else 20
except Exception:
    reading_goal = 20
    
books_read_count = len(df[df["Shelf"] == "Books I've Read"])
books_owned_count = len(df[df["Shelf"] == "Books I Own"])
tbr_count = len(df[df["Shelf"] == "Books I Want to Read"])
READING_GOAL = 20

stat1, stat2, stat3 = st.columns(3)
stat1.metric("🐉 Owned", books_owned_count)
stat2.metric("✨ Want to Read", tbr_count)
stat3.metric("💖 Completed", f"{books_read_count} / {READING_GOAL}")
st.progress(min(books_read_count / READING_GOAL, 1.0))

with st.expander("🎯 Set My Reading Goal", expanded=False):
    new_goal = st.number_input("How many books do you want to read?", min_value = 1, max_value = 10000, value=reading_goal, step=1)
    if st.button("Update Goal ✨", use_container_width=True):
        try: 
            g_df = conn.read(worksheet="DragonStats", ttl=0)
            g_df.at[0, "Goal"] = int(new_goal)
            conn.update(worksheet="DragonStats", data=g_df)
            st.success(f"Reading goal updated to {int(new_goal)} books!")
            st.rerun()
        except Exception:
            st.warning("Make sure cell E1 in DragonStats is named 'Goal'!")
            
# Put Dragon's Whimsy first if she tapped the Willow Stand!
if door == "willow":
    tab_whimsy, tab1, tab2, tab3 = st.tabs([
        "💌 Dragon's Whimsy", "🐉 Books I Own", "✨ Books I Want to Read", "💖 Books I've Read"
    ])
else:
    tab1, tab2, tab3, tab_whimsy = st.tabs([
        "🐉 Books I Own", "✨ Books I Want to Read", "💖 Books I've Read", "💌 Dragon's Whimsy"
    ])

# --- Add a New Book Form ---
with st.expander("✨ Add a New Book to the Hoard", expanded=False):
    with st.form("add_book_form", clear_on_submit=True):
        title = st.text_input("Book Title")
        author = st.text_input("Author")
        shelf = st.selectbox("Which Shelf?", SHELVES)
        rating = st.select_slider(
            "Dragon Egg Rating",
            options=["🥚", "🥚🥚", "🥚🥚🥚", "🥚🥚🥚🥚", "🥚🥚🥚🥚🥚"],
            value="🥚🥚🥚🥚🥚"
        )
        notes = st.text_area("Thoughts or Favorite Quotes")
        submitted = st.form_submit_button("Add to Hoard 🌸")

        if submitted and title:
            with st.spinner("Summoning book cover..."):
                cover_url = fetch_book_cover(title, author)
            new_book = pd.DataFrame([{
                "Title": title,
                "Author": author,
                "Shelf": shelf,
                "Rating": rating,
                "Notes": notes,
                "CoverURL": cover_url
            }])
            df = pd.concat([df, new_book], ignore_index=True)
            save_books(df)
            st.success(f"Added '{title}' to {shelf}!")
            st.rerun()

# --- Search & Random TBR Picker ---
search_query = st.text_input("🔍 Search your shelves by title or author", placeholder="Type a title or author...")

# --- Display Books Function ---
def show_shelf(shelf_name, tab):
    global df
    with tab:
        shelf_books = df[df["Shelf"] == shelf_name]

        # Random Next-Read Picker on Books I Want to Read tab
        if shelf_name == "Books I Want to Read" and not shelf_books.empty:
            if st.button("🎲 Can't decide? Let the dragon pick my next read!", use_container_width=True):
                pick = shelf_books.sample(1).iloc[0]
                st.balloons()
                st.success(f"🐉 Your dragon picked: **{pick['Title']}** by *{pick['Author']}*!")

        if search_query:
            q = search_query.lower()
            shelf_books = shelf_books[
                shelf_books["Title"].str.lower().str.contains(q, na=False) |
                shelf_books["Author"].str.lower().str.contains(q, na=False)
            ]

        if shelf_books.empty:
            st.info(f"No books in '{shelf_name}' yet. Add one above!")
        else:
            for idx, row in shelf_books.iterrows():
                col_cover, col_info = st.columns(2)
                cover_url = str(row.get("CoverURL", "")).strip()
                with col_cover:
                    if cover_url.startswith("http"):
                        st.image(cover_url, width=120)
                    else:
                        st.markdown("## 📖")
                with col_info:
                    st.subheader(f"{row['Title']} — *{row['Author']}*")
                    st.write(f"**Rating:** {row['Rating']}")
                    if pd.notna(row["Notes"]) and row["Notes"]:
                        st.write(f"*{row['Notes']}*")

                    other_shelves = [s for s in SHELVES if s != shelf_name]
                    first_shelf = next(iter(other_shelves))
                    second_shelf = other_shelves[-1]

                    if st.button(f"Move to {first_shelf}", key=f"m1_{idx}", use_container_width=True):
                        df.at[idx, "Shelf"] = first_shelf
                        save_books(df)
                        st.rerun()

                    if st.button(f"Move to {second_shelf}", key=f"m2_{idx}", use_container_width=True):
                        df.at[idx, "Shelf"] = second_shelf
                        save_books(df)
                        st.rerun()

                    if st.button("🗑️ Remove Book", key=f"del_{idx}", use_container_width=True):
                        df = df.drop(idx).reset_index(drop=True)
                        save_books(df)
                        st.rerun()
                st.divider()

show_shelf("Books I Own", tab1)
show_shelf("Books I Want to Read", tab2)
show_shelf("Books I've Read", tab3)

# --- Dragon's Whimsy Tab ---
with tab_whimsy:
    st.subheader("🌸 Notes, Date Ideas & Coupons 🐉")

    love_notes = [
        "Just a reminder that you're my favorite person to spend time with. 💖",
        "Hope your day is going smoothly—can't wait to see you later. 🌸",
        "You make ordinary days feel way better just by being around. ✨",
        "Take a second to relax today—you've earned it. 🌷",
        "Still my favorite adventure partner. 💕",
        "Random reminder that I appreciate everything you do. 💖",]
