import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
import random

# Page setup
st.set_page_config(page_title="The Dragon's Sanctuary", page_icon="🐉")

# --- Whimsical Fairy Background & Falling Petals ---
st.markdown("""
<style>
.stApp {
    background: linear-gradient(180deg, #FFE4EC 0%, #FFB6C1 48%, #E1BEE7 100%);
    background-attachment: fixed;
}
.stApp h1, .stApp h2, .stApph3, .stApp p, .stApp label, .stApp span, .stApp div {
    color: #9C1B5B !important;
}
[data-testid="stExpander"] {
    background-color: rgba(255, 255, 255, 0.78);
    border: 1.5px solid #FF69B4;
    border-radius: 18px;
    box-shadow: 0 4px 15px rgba(255, 105, 180, 0.15);
}
.stButton > button {
    border-radius: 20px;
    border: 1px solid #FF69B4;
    background-color: #FFF5F8;
    color: #4A2545;
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
<div class="petal" style="left: 65%; animation-duration: 15s; animation-delay: 4s;">❤️</div>
<div class="petal" style="left: 65%; animation-duration: 15s; animation-delay: 4s;">🐉</div>
<div class="petal" style="left: 82%; animation-duration: 10s; animation-delay: 2s;">✨</div>
<div class="petal" style="left: 93%; animation-duration: 13s; animation-delay: 5s;">🌸</div>
""", unsafe_allow_html=True)

st.title("🐉 The Dragon's Sanctuary 🌸")

# Detect which NFC door she tapped (?door=willow vs ?door=books)
door = st.query_params.get("door", "books")
if door == "willow":
    st.info("🌸 Welcome back from your Willow Tree Jewelry Stand! Tap **💌 Dragon's Whimsy** for a surprise.")

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
    try:
        query = f"{title} {author}".strip()
        url = f"https://openlibrary.org{requests.utils.quote(query)}&limit=1"
        response = requests.get(url, timeout=5)
        docs = response.json().get("docs", [])
        if docs and "cover_i" in docs[0]:
            return f"https://openlibrary.org{docs[0]['cover_i']}-M.jpg"
    except Exception:
        pass
    return ""

# Put Dragon's Whimsy first if she tapped the Willow Stand!
if door == "willow":
    tab_whimsy, tab1, tab2, tab3 = st.tabs([
        "💌 Dragon's Whimsy", "🐉 Books I Own", "✨ Books I Want to Read", "❤️ Books I've Read"
    ])
else:
    tab1, tab2, tab3, tab_whimsy = st.tabs([
        "🐉 Books I Own", "✨ Books I Want to Read", "❤️ Books I've Read", "💌 Dragon's Whimsy"
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
        notes = st.text_area("Whimsical Thoughts or Quotes")
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

# --- Display Books Function ---
def show_shelf(shelf_name, tab):
    global df
    with tab:
        shelf_books = df[df["Shelf"] == shelf_name]
        if shelf_books.empty:
            st.info(f"No books in '{shelf_name}' yet. Add one above!")
        else:
            for idx, row in shelf_books.iterrows():
                col_cover, col_info = st.columns([1, 3])
                with col_cover:
                    if pd.notna(row.get("CoverURL")) and str(row["CoverURL"]).startswith("http"):
                        st.image(row["CoverURL"], width=110)
                    else:
                        st.markdown("## 📖")
                with col_info:
                    st.subheader(f"{row['Title']} — *{row['Author']}*")
                    st.write(f"**Rating:** {row['Rating']}")
                    if pd.notna(row["Notes"]) and row["Notes"]:
                        st.write(f"*{row['Notes']}*")

                    other_shelves = [s for s in SHELVES if s != shelf_name]
                    btn_col1, btn_col2, btn_col3 = st.columns([2, 2, 1.5])
                    with btn_col1:
                        if st.button(f"Move to {other_shelves[0]}", key=f"m1_{idx}"):
                            df.at[idx, "Shelf"] = other_shelves[0]
                            save_books(df)
                            st.rerun()
                    with btn_col2:
                        if st.button(f"Move to {other_shelves[1]}", key=f"m2_{idx}"):
                            df.at[idx, "Shelf"] = other_shelves[1]
                            save_books(df)
                            st.rerun()
                    with btn_col3:
                        if st.button("🗑️", key=f"del_{idx}", help="Remove Book"):
                            df = df.drop(idx).reset_index(drop=True)
                            save_books(df)
                            st.rerun()
                st.divider()

show_shelf("Books I Own", tab1)
show_shelf("Want to Read", tab2)
show_shelf("Books I've Read", tab3)

# --- Dragon's Whimsy Tab ---
with tab_whimsy:
    st.subheader("🌸 A Secret Note from Your Guardian Dragon 🐉")
    st.write("Tap a button below whenever you open the willow tree fairy door!")

    love_notes = [
        "You are my favorite treasure in every realm. 💖",
        "Even a fierce dragon couldn't guard something as precious as you. 🐉🌸",
        "Just a reminder that you make my whole world brighter every single day. ✨",
        "Here is your fairy blessing for today: extra cozy vibes, good books, and endless smiles! 🌷",
        "I love you more than dragons love shiny gold. 💕"
    ]

    date_ideas = [
        "📚 Cozy bookstore date + pink drinks afterward!",
        "🍿 Blanket fort fantasy movie marathon with snacks!",
        "🌸 Picnic under the trees with pastries and books!",
        "🎨 Paint-and-sip night at home while listening to fantasy soundtracks!",
        "🍜 Dinner at your favorite spot + stargazing walk!"
    ]

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("💌 Draw a Love Note", use_container_width=True):
            st.balloons()
            st.success(random.choice(love_notes))
    with col_b:
        if st.button("✨ Spin Whimsical Date Idea", use_container_width=True):
            st.info(random.choice(date_ideas))

    st.divider()
    if st.button("🥚 Pet the Pink Baby Dragon", use_container_width=True):
        st.toast("The baby pink dragon purrs happily and blows a tiny heart-shaped smoke ring! 💕🐉")


