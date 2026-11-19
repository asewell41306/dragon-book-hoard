import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
import random
import time
from datetime import datetime
from zoneinfo import ZoneInfo

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

# Central Time Greeting
hour = datetime.now(ZoneInfo("America/Chicago")).hour
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

df = conn.read(worksheet="Sheet1", ttl=300)
if df.empty or list(df.columns) != COLUMNS:
    df = pd.DataFrame(columns=COLUMNS)
else:
    df = df.dropna(how="all")

def save_books(updated_df):
    conn.update(worksheet="Sheet1", data=updated_df)
    st.cache_data.clear()

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

# Read DragonStats once
try:
    stats_df = conn.read(worksheet="DragonStats", ttl=300)
    sheet_love = int(float(stats_df.at[0, "Love"])) if "Love" in stats_df.columns and not stats_df.empty and pd.notna(stats_df.at[0, "Love"]) else 0
    last_fed = float(stats_df.at[0, "LastFed"]) if "LastFed" in stats_df.columns and not stats_df.empty and pd.notna(stats_df.at[0, "LastFed"]) else time.time()
    sheet_name = str(stats_df.at[0, "Name"]) if "Name" in stats_df.columns and not stats_df.empty and pd.notna(stats_df.at[0, "Name"]) else "Baby Dragon"
    sheet_acc = str(stats_df.at[0, "Accessory"]) if "Accessory" in stats_df.columns and not stats_df.empty and pd.notna(stats_df.at[0, "Accessory"]) else "None"
    sheet_goal = int(float(stats_df.at[0, "Goal"])) if "Goal" in stats_df.columns and not stats_df.empty and pd.notna(stats_df.at[0, "Goal"]) else 20
    sheet_col = str(stats_df.at[0, "Color"]) if "Color" in stats_df.columns and not stats_df.empty and pd.notna(stats_df.at[0, "Color"]) else "🌸 Sakura Pink"
    sheet_bg = str(stats_df.at[0, "Background"]) if "Background" in stats_df.columns and not stats_df.empty and pd.notna(stats_df.at[0, "Background"]) else "🌙 Starlight Meadow"
except Exception:
    sheet_love, last_fed, sheet_name, sheet_acc, sheet_goal, sheet_col, sheet_bg = 0, time.time(), "Baby Dragon", "None", 20, "🌸 Sakura Pink", "🌙 Starlight Meadow"

reading_goal = st.session_state.get("cached_goal", sheet_goal)
love = st.session_state.get("cached_love", sheet_love)
dragon_name = st.session_state.get("cached_name", sheet_name)
accessory = st.session_state.get("cached_acc", sheet_acc)
dragon_color = st.session_state.get("cached_col", sheet_col)
dragon_bg = st.session_state.get("cached_bg", sheet_bg)

def save_dragon_stats(new_love=love, new_name=dragon_name, new_acc=accessory, new_goal=reading_goal, new_col=dragon_color, new_bg=dragon_bg, reset_timer=True):
    st.session_state.cached_love = new_love
    st.session_state.cached_name = new_name
    st.session_state.cached_acc = new_acc
    st.session_state.cached_goal = new_goal
    st.session_state.cached_col = new_col
    st.session_state.cached_bg = new_bg
    if reset_timer:
        st.session_state.cached_last_fed = time.time()
    try:
        new_df = pd.DataFrame([{
            "Love": new_love,
            "LastFed": st.session_state.get("cached_last_fed", time.time()),
            "Name": new_name,
            "Accessory": new_acc,
            "Goal": new_goal,
            "Color": new_col,
            "Background": new_bg
        }])
        conn.update(worksheet="DragonStats", data=new_df)
    except Exception:
        pass

# --- Hoard Stats & Custom Reading Goal Bar (Supports Multi-Shelf Books) ---
shelf_series = df["Shelf"].fillna("").astype(str)
books_owned_count = shelf_series.str.contains("Books I Own", regex=False).sum()
tbr_count = shelf_series.str.contains("Books I Want to Read", regex=False).sum()
books_read_count = shelf_series.str.contains("Books I've Read", regex=False).sum()

stat1, stat2, stat3 = st.columns(3)
stat1.metric("🐉 Owned", int(books_owned_count))
stat2.metric("✨ Want to Read", int(tbr_count))
stat3.metric("💖 Completed", f"{int(books_read_count)} / {reading_goal}")
st.progress(min(books_read_count / max(reading_goal, 1), 1.0))

with st.expander("🎯 Set My Reading Goal", expanded=False):
    new_goal = st.number_input("How many books do you want to read?", min_value=1, max_value=500, value=reading_goal, step=1)
    if st.button("Update Goal ✨", use_container_width=True):
        save_dragon_stats(new_goal=int(new_goal), reset_timer=False)
        st.success(f"Reading goal updated to {int(new_goal)} books!")
        st.rerun()

# Put Dragon's Whimsy first if she tapped the Willow Stand!
if door == "willow":
    tab_whimsy, tab1, tab2, tab3 = st.tabs([
        "💌 Dragon's Whimsy", "🐉 Books I Own", "✨ Books I Want to Read", "💖 Books I've Read"
    ])
else:
    tab1, tab2, tab3, tab_whimsy = st.tabs([
        "🐉 Books I Own", "✨ Books I Want to Read", "💖 Books I've Read", "💌 Dragon's Whimsy"
    ])

# --- Add a New Book Form (Multi-Shelf Enabled!) ---
with st.expander("✨ Add a New Book to the Hoard", expanded=False):
    with st.form("add_book_form", clear_on_submit=True):
        title = st.text_input("Book Title")
        author = st.text_input("Author")
        chosen_shelves = st.multiselect(
            "Which Shelf or Shelves? (Pick one or multiple!)",
            SHELVES,
            default=["Books I Own"]
        )
        rating = st.select_slider(
            "Dragon Egg Rating",
            options=["🥚", "🥚🥚", "🥚🥚🥚", "🥚🥚🥚🥚", "🥚🥚🥚🥚🥚"],
            value="🥚🥚🥚🥚🥚"
        )
        notes = st.text_area("Thoughts or Favorite Quotes")
        submitted = st.form_submit_button("Add to Hoard 🌸")

        if submitted and title:
            if not chosen_shelves:
                chosen_shelves = ["Books I Own"]
            with st.spinner("Summoning book cover..."):
                cover_url = fetch_book_cover(title, author)
            shelf_str = ", ".join(chosen_shelves)
            new_book = pd.DataFrame([{
                "Title": title,
                "Author": author,
                "Shelf": shelf_str,
                "Rating": rating,
                "Notes": notes,
                "CoverURL": cover_url
            }])
            df = pd.concat([df, new_book], ignore_index=True)
            save_books(df)

            # +5 Dragon XP bonus if she finished the book!
            if "Books I've Read" in chosen_shelves:
                save_dragon_stats(new_love=love + 5)
                st.success(f"Added '{title}' & gave {dragon_name} +5 XP for finishing a book! 🐉✨")
            else:
                st.success(f"Added '{title}' to {shelf_str}!")
            st.rerun()

# --- Search Bar ---
search_query = st.text_input("🔍 Search your shelves by title or author", placeholder="Type a title or author...")

# --- Display Books Function (Supports Multiple Shelves per Book) ---
def show_shelf(shelf_name, tab):
    global df
    with tab:
        shelf_books = df[df["Shelf"].fillna("").astype(str).str.contains(shelf_name, regex=False)]

        if shelf_name == "Books I Want to Read" and not shelf_books.empty:
            if st.button("🎲 Can't decide? Let the dragon pick my next read!", use_container_width=True):
                pick = shelf_books.sample(1).iloc
                st.balloons()
                st.success(f"🐉 {dragon_name} picked: **{pick['Title']}** by *{pick['Author']}*!")

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

                    current_list = [s.strip() for s in str(row["Shelf"]).split(",") if s.strip() in SHELVES]
                    updated_list = st.multiselect(
                        "Shelves:",
                        SHELVES,
                        default=current_list,
                        key=f"ms_{shelf_name}_{idx}"
                    )

                    b_col1, b_col2 = st.columns(2)
                    with b_col1:
                        if st.button("💾 Save Shelves", key=f"sv_{shelf_name}_{idx}", use_container_width=True):
                            if not updated_list:
                                st.warning("Keep at least one shelf selected (or click Remove).")
                            else:
                                was_read = "Books I've Read" in current_list
                                now_read = "Books I've Read" in updated_list
                                df.at[idx, "Shelf"] = ", ".join(updated_list)
                                save_books(df)
                                if not was_read and now_read:
                                    save_dragon_stats(new_love=love + 5)
                                    st.toast(f"+5 XP to {dragon_name} for finishing a book! 🐉")
                                st.rerun()
                    with b_col2:
                        if st.button("🗑️ Remove", key=f"del_{shelf_name}_{idx}", use_container_width=True):
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
        "Random reminder that I appreciate everything you do. 💖",
        "Drink some water, grab a snack, and know I'm rooting for you today! 🌸",
        "If I had to pick one person to get stuck in a bookstore with forever, it's easily you. 📖💕",
        "You deserve a super cozy, stress-free day today. ✨",
        "Redeem this note anytime for one extra-long hug and your favorite drink. 🎟️💖"
    ]

    date_ideas = [
        "📚 Bookstore browse + iced coffee run afterward",
        "🍿 Cozy movie marathon on the couch with all your favorite snacks",
        "🌸 Picnic in the park with pastries and a good book",
        "🎨 At-home paint night with takeout and a good playlist",
        "🍜 Dinner at your favorite spot + an evening walk",
        "🧁 Bake something from scratch together at home",
        "🚗 Sunset drive with good music and milkshakes",
        "🛍️ Thrift-store challenge: pick out cozy outfits for each other under $20",
        "🎲 Board game or co-op video game night",
        "🎟️ Mystery date night—you pick cozy or fancy, and I'll handle the rest"
    ]

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("💌 Draw a Note", use_container_width=True):
            st.balloons()
            st.success(random.choice(love_notes))
    with col_b:
        if st.button("✨ Spin Date Idea", use_container_width=True):
            st.info(random.choice(date_ideas))

    # --- Open When Letters ---
    st.write("")
    open_when = st.selectbox("✉️ Open When...", [
        "Choose a letter to open...",
        "Open when you're having a stressful day",
        "Open when you just finished a great book",
        "Open when you miss me",
        "Open when you can't decide what to do tonight"
    ])

    open_when_messages = {
        "Open when you're having a stressful day": "Take a deep breath and drop your shoulders. Whatever is stressing you out today is temporary—text me if you want to vent, or let me bring you dinner tonight so you don't have to cook. 💖",
        "Open when you just finished a great book": "Check off 'Books I've Read' on your shelf right now (+5 Dragon XP!)—and whenever you're ready, I want to hear all about it. 📖✨",
        "Open when you miss me": "I miss you too! Send me a text right now so we can plan when we're hanging out next. 💕",
        "Open when you can't decide what to do tonight": "Hit the 'Spin Date Idea' button right above this, or cash in one of your treat coupons below—my treat! 🐉"
    }
    if open_when in open_when_messages:
        st.info(open_when_messages[open_when])

    # --- Redeemable Treat Coupons ---
    with st.expander("🎟️ Redeem a Treat Coupon", expanded=False):
        coupon_choice = st.selectbox("Pick a coupon to cash in:", [
            "☕ 1 Free Iced Coffee / Favorite Drink Delivery",
            "🎬 Complete Movie Night Pick (No Vetoes)",
            "💆‍♀️ 15-Minute Back or Shoulder Rub",
            "🥡 Dinner Takeout of Your Choice",
            "📚 $20 Bookstore Gift Card / Book Run"
        ])
        if st.button("Redeem Coupon Now 🌸", use_container_width=True):
            try:
                c_df = conn.read(worksheet="Coupons", ttl=300)
                new_c = pd.DataFrame([{
                    "Coupon": coupon_choice,
                    "RedeemedAt": datetime.now(ZoneInfo("America/Chicago")).strftime("%Y-%m-%d %I:%M %p")
                }])
                c_df = pd.concat([c_df, new_c], ignore_index=True)
                conn.update(worksheet="Coupons", data=c_df)
            except Exception:
                pass
            st.balloons()
            st.success(f"Redeemed: **{coupon_choice}**! Screenshot this or let me know so I can deliver! 💖")

    st.divider()

    if "dragon_msg" not in st.session_state:
        st.session_state.dragon_msg = ""
    if "dragon_action" not in st.session_state:
        st.session_state.dragon_action = ""

    # --- Loneliness / Sadness Calculation Over Time ---
    active_last_fed = st.session_state.get("cached_last_fed", last_fed)
    hours_alone = (time.time() - active_last_fed) / 3600 if active_last_fed > 0 else 0

    if love == 0:
        loneliness = "egg"
    elif hours_alone >= 48:
        loneliness = "very_sad"
    elif hours_alone >= 24:
        loneliness = "lonely"
    else:
        loneliness = "happy"

    # --- Clear 5-Level Progression System (5 XP per level) ---
    if love == 0:
        level = 0
        stage_title = "🥚 Sleeping Egg"
        next_unlock = "Tap Pet or Feed Berry to hatch Level 1!"
        xp_progress = 0.0
    elif love < 5:
        level = 1
        stage_title = "Level 1 • 🐣 Tiny Hatchling"
        next_unlock = f"Next Unlock at Level 2 ({5 - love} XP away): 🌸 Flower Crown & 🧣 Cozy Scarf"
        xp_progress = love / 5.0
    elif love < 10:
        level = 2
        stage_title = "Level 2 • ✨ Curious Fledgling"
        next_unlock = f"Next Unlock at Level 3 ({10 - love} XP away): 👓 Reading Glasses & ☕ Tiny Mug"
        xp_progress = (love - 5) / 5.0
    elif love < 15:
        level = 3
        stage_title = "Level 3 • 📖 Bookworm Drake"
        next_unlock = f"Next Unlock at Level 4 ({15 - love} XP away): 🧙‍♀️ Witch Hat, 📖 Mini-Book & Backgrounds"
        xp_progress = (love - 10) / 5.0
    elif love < 20:
        level = 4
        stage_title = "Level 4 • 🌟 Enchanted Guardian"
        next_unlock = f"Next Unlock at Level 5 ({20 - love} XP away): 👑 Royal Crown & Golden Aura"
        xp_progress = (love - 15) / 5.0
    else:
        level = 5
        stage_title = "Level 5 • 👑 Royal Sanctuary Dragon"
        next_unlock = "Max Level Reached! All outfits, backgrounds & royal aura unlocked ✨"
        xp_progress = 1.0

    st.subheader(f"🐉 {dragon_name} — {stage_title}")

    # Color palettes (body, wing, belly, outline)
    palettes = {
        "🌸 Sakura Pink": ("#FFB6C1", "#FF9EBB", "#FFE4EC", "#FF69B4"),
        "💜 Lavender Mist": ("#D8BFD8", "#C39BD3", "#F5EEF8", "#8E44AD"),
        "🩵 Mint Fairy": ("#A3E4D7", "#76D7C4", "#E8F8F5", "#1ABC9C"),
        "🍑 Peach Blossom": ("#FAD7A0", "#F8C471", "#FEF5E7", "#E67E22"),
        "🤍 Pearl White": ("#F8F9F9", "#E5E7E9", "#FFFFFF", "#D98880")
    }
    body_c, wing_c, belly_c, line_c = palettes.get(dragon_color, palettes["🌸 Sakura Pink"])

    # Selectable Backgrounds
    if dragon_bg == "🌸 Cherry Blossom Grove":
        bg_svg = """
        <defs><linearGradient id="skyGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#FFE0EC"/><stop offset="100%" stop-color="#FFC1D6"/></linearGradient></defs>
        <rect x="0" y="0" width="220" height="200" rx="22" fill="url(#skyGrad)" stroke="#FF69B4" stroke-width="3"/>
        <circle cx="38" cy="38" r="16" fill="#FFF59D" opacity="0.85"/>
        <text x="165" y="42" font-size="22">🌸</text><text x="22" y="75" font-size="16">🌸</text><text x="180" y="95" font-size="15">🌸</text>
        <path d="M0 165 Q65 145 120 162 Q175 148 220 162 L220 200 L0 200 Z" fill="#F8BBD0"/>
        <rect x="18" y="168" width="34" height="8" rx="2" fill="#CE93D8" stroke="#8E24AA" stroke-width="1.5"/>
        <rect x="21" y="160" width="30" height="8" rx="2" fill="#F48FB1" stroke="#C2185B" stroke-width="1.5"/>
        """
    elif dragon_bg == "📚 Cozy Library":
        bg_svg = """
        <rect x="0" y="0" width="220" height="200" rx="22" fill="#F3E5F5" stroke="#8E24AA" stroke-width="3"/>
        <rect x="14" y="18" width="52" height="145" rx="4" fill="#E1BEE7" stroke="#BA68C8" stroke-width="2"/>
        <line x1="14" y1="55" x2="66" y2="55" stroke="#BA68C8" stroke-width="2"/>
        <line x1="14" y1="95" x2="66" y2="95" stroke="#BA68C8" stroke-width="2"/>
        <rect x="20" y="33" width="8" height="22" fill="#F06292"/><rect x="30" y="36" width="8" height="19" fill="#9575CD"/><rect x="40" y="31" width="9" height="24" fill="#4DB6AC"/>
        <rect x="22" y="73" width="9" height="22" fill="#FFB74D"/><rect x="34" y="75" width="8" height="20" fill="#F06292"/>
        <circle cx="182" cy="40" r="14" fill="#FFF59D" opacity="0.9"/>
        <text x="174" y="45" font-size="14">🕯️</text>
        <path d="M0 168 L220 168 L220 200 L0 200 Z" fill="#CE93D8" opacity="0.6"/>
        """
    else:
        bg_svg = """
        <defs><linearGradient id="skyGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#FCE4EC"/><stop offset="100%" stop-color="#E1BEE7"/></linearGradient></defs>
        <rect x="0" y="0" width="220" height="200" rx="22" fill="url(#skyGrad)" stroke="#FF69B4" stroke-width="3"/>
        <circle cx="180" cy="36" r="14" fill="#FFF9C4" opacity="0.9"/>
        <circle cx="185" cy="33" r="12" fill="#FCE4EC"/>
        <text x="25" y="35" font-size="12" opacity="0.8">✨</text><text x="135" y="28" font-size="11" opacity="0.8">✨</text>
        <path d="M0 165 Q65 142 120 162 Q175 145 220 160 L220 200 L0 200 Z" fill="#F8BBD0" opacity="0.7"/>
        <path d="M0 175 Q90 158 220 175 L220 200 L0 200 Z" fill="#F48FB1" opacity="0.55"/>
        <rect x="18" y="168" width="34" height="8" rx="2" fill="#CE93D8" stroke="#8E24AA" stroke-width="1.5"/>
        <rect x="21" y="160" width="30" height="8" rx="2" fill="#F48FB1" stroke="#C2185B" stroke-width="1.5"/>
        """

    action_svg = ""
    if st.session_state.dragon_action == "pet":
        action_svg = '<text x="35" y="65" font-size="24">💕</text><text x="155" y="60" font-size="22">💖</text><text x="145" y="105" font-size="18">✨</text>'
    elif st.session_state.dragon_action == "berry":
        action_svg = '<text x="32" y="135" font-size="26">🍓</text><text x="152" y="75" font-size="20">😋</text><text x="155" y="135" font-size="22">🍓</text>'
    elif st.session_state.dragon_action == "gem":
        action_svg = '<text x="30" y="135" font-size="26">💎</text><text x="152" y="65" font-size="22">✨</text><text x="152" y="135" font-size="26">💎</text>'

    if love == 0:
        dragon_svg = f"""
        <div style="text-align:center; margin: 10px 0;">
          <svg width="220" height="200" viewBox="0 0 220 200">
            {bg_svg}
            <ellipse cx="110" cy="118" rx="46" ry="58" fill="{belly_c}" stroke="{line_c}" stroke-width="4"/>
            <path d="M68 110 L88 98 L108 112 L128 96 L152 108" fill="none" stroke="{line_c}" stroke-width="4" stroke-linecap="round"/>
            <circle cx="92" cy="138" r="6" fill="{wing_c}"/>
            <circle cx="130" cy="86" r="5" fill="{wing_c}"/>
            <text x="145" y="62" font-size="22">💤</text>
          </svg>
        </div>
        """
    else:
        # Scale & wings grow clearly at each level
        scales_by_lvl = {1: "0.84", 2: "0.90", 3: "0.96", 4: "1.02", 5: "1.08"}
        scale = scales_by_lvl.get(level, "0.90")

        if level <= 2:
            wings = f'<path d="M68 108 Q42 88 55 120 Q48 130 70 126 Z" fill="{wing_c}" stroke="{line_c}" stroke-width="3"/><path d="M152 108 Q178 88 165 120 Q172 130 150 126 Z" fill="{wing_c}" stroke="{line_c}" stroke-width="3"/>'
        elif level <= 4:
            wings = f'<path d="M66 105 Q22 65 44 122 Q34 138 68 132 Z" fill="{wing_c}" stroke="{line_c}" stroke-width="3"/><path d="M154 105 Q198 65 176 122 Q186 138 152 132 Z" fill="{wing_c}" stroke="{line_c}" stroke-width="3"/>'
        else:
            wings = f'<path d="M65 102 Q10 48 36 124 Q24 144 68 134 Z" fill="{wing_c}" stroke="#FFD700" stroke-width="3.5"/><path d="M155 102 Q210 48 184 124 Q196 144 152 134 Z" fill="{wing_c}" stroke="#FFD700" stroke-width="3.5"/>'

        # Facial expressions based on loneliness
        if loneliness == "very_sad":
            eyes = '<path d="M88 76 Q96 83 103 78" fill="none" stroke="#4A2545" stroke-width="3.5" stroke-linecap="round"/><path d="M117 78 Q124 83 132 76" fill="none" stroke="#4A2545" stroke-width="3.5" stroke-linecap="round"/><ellipse cx="86" cy="87" rx="3" ry="5" fill="#64B5F6"/><ellipse cx="134" cy="87" rx="3" ry="5" fill="#64B5F6"/>'
            mouth = '<path d="M102 99 Q110 91 118 99" fill="none" stroke="#4A2545" stroke-width="3" stroke-linecap="round"/>'
            anim_speed = "4.5s"
        elif loneliness == "lonely":
            eyes = '<circle cx="96" cy="78" r="4" fill="#4A2545"/><circle cx="124" cy="78" r="4" fill="#4A2545"/>'
            mouth = '<line x1="103" y1="96" x2="117" y2="96" stroke="#4A2545" stroke-width="3" stroke-linecap="round"/>'
            anim_speed = "3.4s"
        else:
            eyes = '<path d="M90 80 Q96 72 102 80" fill="none" stroke="#4A2545" stroke-width="3.5" stroke-linecap="round"/><path d="M118 80 Q124 72 130 80" fill="none" stroke="#4A2545" stroke-width="3.5" stroke-linecap="round"/>'
            mouth = '<path d="M103 93 Q110 100 117 93" fill="none" stroke="#4A2545" stroke-width="3" stroke-linecap="round"/>'
            anim_speed = "2.1s"

        # Bookish & Royal Accessories
        acc_svg = ""
        if accessory == "👑 Royal Crown" or (accessory == "None" and level >= 5):
            acc_svg = '<polygon points="92,42 100,25 110,38 120,25 128,42" fill="#FFD700" stroke="#E6AC00" stroke-width="2"/>'
        elif accessory == "🌸 Flower Crown":
            acc_svg = '<circle cx="92" cy="44" r="7" fill="#FF69B4"/><circle cx="110" cy="41" r="8" fill="#FFB6C1"/><circle cx="128" cy="44" r="7" fill="#FF69B4"/><circle cx="110" cy="41" r="3" fill="#FFD700"/>'
        elif accessory == "👓 Reading Glasses":
            acc_svg = '<circle cx="96" cy="78" r="10" fill="none" stroke="#4A2545" stroke-width="2.5"/><circle cx="124" cy="78" r="10" fill="none" stroke="#4A2545" stroke-width="2.5"/><line x1="106" y1="78" x2="114" y2="78" stroke="#4A2545" stroke-width="2.5"/>'
        elif accessory == "🧙‍♀️ Witch Hat":
            acc_svg = '<ellipse cx="110" cy="46" rx="36" ry="7" fill="#6A1B9A" stroke="#4A148C" stroke-width="2"/><polygon points="88,46 112,10 132,46" fill="#7B1FA2" stroke="#4A148C" stroke-width="2"/><text x="104" y="36" font-size="11">⭐</text>'
        elif accessory == "🧣 Cozy Scarf":
            acc_svg = '<rect x="82" y="112" width="56" height="11" rx="5" fill="#F06292" stroke="#C2185B" stroke-width="2"/><rect x="122" y="118" width="12" height="24" rx="4" fill="#F48FB1" stroke="#C2185B" stroke-width="2"/>'
        elif accessory == "☕ Tiny Mug":
            acc_svg = '<rect x="148" y="128" width="16" height="18" rx="3" fill="#FFF8E1" stroke="#8D6E63" stroke-width="2"/><path d="M164 132 Q171 137 164 142" fill="none" stroke="#8D6E63" stroke-width="2"/><text x="150" y="123" font-size="11">♨️</text>'
        elif accessory == "📖 Open Mini-Book":
            acc_svg = '<path d="M84 145 Q97 140 110 146 Q123 140 136 145 L136 162 Q123 157 110 163 Q97 157 84 162 Z" fill="#FFFDF9" stroke="#8E24AA" stroke-width="2"/><line x1="110" y1="146" x2="110" y2="163" stroke="#8E24AA" stroke-width="1.5"/>'

        dragon_svg = f"""
        <style>
        @keyframes dragonBounce {{
            0%, 100% {{ transform: translateY(0px) scale({scale}); }}
            50% {{ transform: translateY(-6px) scale({scale}); }}
        }}
        .baby-dragon {{ transform-origin: 110px 130px; animation: dragonBounce {anim_speed} ease-in-out infinite; }}
        </style>
        <div style="text-align:center; margin: 10px 0;">
          <svg width="220" height="200" viewBox="0 0 220 200">
            {bg_svg}
            <g class="baby-dragon">
              {wings}
              <path d="M145 155 Q185 155 180 130 Q175 120 165 130" fill="none" stroke="{line_c}" stroke-width="8" stroke-linecap="round"/>
              <ellipse cx="110" cy="135" rx="42" ry="45" fill="{body_c}" stroke="{line_c}" stroke-width="3.5"/>
              <ellipse cx="110" cy="140" rx="26" ry="30" fill="{belly_c}"/>
              <circle cx="110" cy="82" r="38" fill="{body_c}" stroke="{line_c}" stroke-width="3.5"/>
              <polygon points="85,52 78,32 96,46" fill="{belly_c}" stroke="{line_c}" stroke-width="3"/>
              <polygon points="135,52 142,32 124,46" fill="{belly_c}" stroke="{line_c}" stroke-width="3"/>
              {eyes}
              <ellipse cx="85" cy="90" rx="7" ry="4" fill="#FF69B4" opacity="0.6"/>
              <ellipse cx="135" cy="90" rx="7" ry="4" fill="#FF69B4" opacity="0.6"/>
              {mouth}
              {acc_svg}
            </g>
            {action_svg}
          </svg>
        </div>
        """

    dragon_svg = "\n".join(line.strip() for line in dragon_svg.splitlines())
    st.markdown(dragon_svg, unsafe_allow_html=True)

    # Mood status reflecting loneliness or happiness
    if loneliness == "egg":
        mood = f"😴 {dragon_name} is fast asleep in her egg (Tap below to hatch her!)"
    elif loneliness == "very_sad":
        mood = f"😢 {dragon_name} missed you so much! Give her a pet or berry to cheer her up."
    elif loneliness == "lonely":
        mood = f"🥺 {dragon_name} is feeling a little lonely waiting for you to visit..."
    else:
        mood = f"💖 {dragon_name} is super happy and watching over your books!"

    st.write(f"**Current Mood:** {mood}")
    st.progress(xp_progress, text=f"Level {level} Progress • Total XP: {love} ✨")
    st.caption(f"🎁 {next_unlock}")

    dragon_reactions = [
        f"{dragon_name} chirps happily and curls her tail around your wrist! 💕🐉",
        f"{dragon_name} sneezes a tiny puff of rose-gold glitter onto your book! ✨🌸",
        f"{dragon_name} rolls over for belly rubs and purrs like a tiny motor! 💖🥚",
        f"{dragon_name} puffs out her chest proudly to guard your favorite books! 📚🐉"
    ]

    d_col1, d_col2, d_col3 = st.columns(3)
    with d_col1:
        if st.button("🥚 Pet (+1 XP)", use_container_width=True):
            new_score = love + 1
            save_dragon_stats(new_love=new_score)
            st.session_state.dragon_msg = random.choice(dragon_reactions)
            st.session_state.dragon_action = "pet"
            if new_score in (5, 10, 15, 20):
                st.balloons()
            st.rerun()
    with d_col2:
        if st.button("🍓 Berry (+2 XP)", use_container_width=True):
            new_score = love + 2
            save_dragon_stats(new_love=new_score)
            st.session_state.dragon_msg = f"Nom nom! {dragon_name} gobbles the sweet berry and cheers right up! 🍓🐉"
            st.session_state.dragon_action = "berry"
            if (love < 5 <= new_score) or (love < 10 <= new_score) or (love < 15 <= new_score) or (love < 20 <= new_score):
                st.balloons()
            st.rerun()
    with d_col3:
        if st.button("💎 Gem (+3 XP)", use_container_width=True):
            new_score = love + 3
            save_dragon_stats(new_love=new_score)
            st.session_state.dragon_msg = f"Ooooh! {dragon_name} adds the sparkling gem to her hoard! 💎✨"
            st.session_state.dragon_action = "gem"
            if (love < 5 <= new_score) or (love < 10 <= new_score) or (love < 15 <= new_score) or (love < 20 <= new_score):
                st.balloons()
            st.rerun()

    if st.session_state.dragon_msg:
        st.info(st.session_state.dragon_msg)

    # --- Dragon Name, Color, Background & Level-Gated Accessory Closet ---
    auto_open_naming = (love > 0 and dragon_name == "Baby Dragon")
    with st.expander(f"🎀 Customize {dragon_name} (Name, Outfits & Sanctuary)", expanded=auto_open_naming):
        new_dragon_name = st.text_input("Dragon's Name:", value="" if dragon_name == "Baby Dragon" else dragon_name, placeholder="Type a name...")

        color_options = ["🌸 Sakura Pink", "💜 Lavender Mist", "🩵 Mint Fairy", "🍑 Peach Blossom", "🤍 Pearl White"]
        chosen_color = st.selectbox("Scale Color:", color_options, index=color_options.index(dragon_color) if dragon_color in color_options else 0)

        bg_options = ["🌙 Starlight Meadow", "🌸 Cherry Blossom Grove", "📚 Cozy Library"]
        chosen_bg = st.selectbox("Sanctuary Background (Unlocks at Level 3+):", bg_options, index=bg_options.index(dragon_bg) if dragon_bg in bg_options else 0)

        acc_options = [
            "None",
            "🌸 Flower Crown",
            "🧣 Cozy Scarf",
            "👓 Reading Glasses",
            "☕ Tiny Mug",
            "🧙‍♀️ Witch Hat",
            "📖 Open Mini-Book",
            "👑 Royal Crown"
        ]
        chosen_acc = st.selectbox("Equip Accessory:", acc_options, index=acc_options.index(accessory) if accessory in acc_options else 0)

        # Level requirements for items
        acc_req = {
            "None": 0,
            "🌸 Flower Crown": 2,
            "🧣 Cozy Scarf": 2,
            "👓 Reading Glasses": 3,
            "☕ Tiny Mug": 3,
            "🧙‍♀️ Witch Hat": 4,
            "📖 Open Mini-Book": 4,
            "👑 Royal Crown": 5
        }

        if st.button("Save Dragon Look ✨", use_container_width=True):
            req_lvl = acc_req.get(chosen_acc, 0)
            if level < req_lvl:
                st.warning(f"{chosen_acc} unlocks at Level {req_lvl}! Pet, feed, or finish books (+5 XP) to level up. 🐉")
            elif chosen_bg != "🌙 Starlight Meadow" and level < 3:
                st.warning("New sanctuary backgrounds unlock at Level 3! 🌙")
            else:
                st.session_state.dragon_action = ""
                save_dragon_stats(
                    new_name=new_dragon_name.strip() or "Baby Dragon",
                    new_acc=chosen_acc,
                    new_col=chosen_color,
                    new_bg=chosen_bg,
                    reset_timer=False
                )
                st.success(f"Updated {new_dragon_name.strip() or 'Baby Dragon'}!")
                st.rerun()
