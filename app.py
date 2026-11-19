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

# --- Hoard Stats & Custom Reading Goal Bar ---
try:
    goal_df = conn.read(worksheet="DragonStats", ttl=300)
    if "Goal" in goal_df.columns and not goal_df.empty and pd.notna(goal_df.at[0, "Goal"]):
        reading_goal = int(float(goal_df.at[0, "Goal"]))
    else:
        reading_goal = 20
except Exception:
    goal_df = pd.DataFrame([{"Love": 0, "LastFed": 0, "Name": "Baby Dragon", "Accessory": "None", "Goal": 20}])
    reading_goal = 20

books_read_count = len(df[df["Shelf"] == "Books I've Read"])
books_owned_count = len(df[df["Shelf"] == "Books I Own"])
tbr_count = len(df[df["Shelf"] == "Books I Want to Read"])

stat1, stat2, stat3 = st.columns(3)
stat1.metric("🐉 Owned", books_owned_count)
stat2.metric("✨ Want to Read", tbr_count)
stat3.metric("💖 Completed", f"{books_read_count} / {reading_goal}")
st.progress(min(books_read_count / max(reading_goal, 1), 1.0))

with st.expander("🎯 Set My Reading Goal", expanded=False):
    new_goal = st.number_input("How many books do you want to read?", min_value=1, max_value=500, value=reading_goal, step=1)
    if st.button("Update Goal ✨", use_container_width=True):
        if goal_df.empty:
            goal_df = pd.DataFrame([{"Love": 0, "LastFed": 0, "Name": "Baby Dragon", "Accessory": "None", "Goal": int(new_goal)}])
        else:
            goal_df.at[0, "Goal"] = int(new_goal)
        conn.update(worksheet="DragonStats", data=goal_df)
        st.cache_data.clear()
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
        "Open when you just finished a great book": "Log your rating on the shelf right now! Whenever you're ready, I want to hear the full spoiler-filled rant about what happened. 📖✨",
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
                    "RedeemedAt": datetime.now().strftime("%Y-%m-%d %I:%M %p")
                }])
                c_df = pd.concat([c_df, new_c], ignore_index=True)
                conn.update(worksheet="Coupons", data=c_df)
            except Exception:
                pass
            st.balloons()
            st.success(f"Redeemed: **{coupon_choice}**! Screenshot this or let me know so I can deliver! 💖")

    st.divider()

    # --- Interactive Baby Dragon Companion ---
     try:
        dragon_df = conn.read(worksheet="DragonStats", ttl=300)
        sheet_love = int(float(dragon_df.at[0, "Love"])) if "Love" in dragon_df.columns and not dragon_df.empty and pd.notna(dragon_df.at[0, "Love"]) else 0
        last_fed = float(dragon_df.at[0, "LastFed"]) if "LastFed" in dragon_df.columns and not dragon_df.empty and pd.notna(dragon_df.at[0, "LastFed"]) else time.time()
        sheet_name = str(dragon_df.at[0, "Name"]) if "Name" in dragon_df.columns and not dragon_df.empty and pd.notna(dragon_df.at[0, "Name"]) else "Baby Dragon"
        sheet_acc = str(dragon_df.at[0, "Accessory"]) if "Accessory" in dragon_df.columns and not dragon_df.empty and pd.notna(dragon_df.at[0, "Accessory"]) else "None"
        sheet_col = str(dragon_df.at[0, "Color"]) if "Color" in dragon_df.columns and not dragon_df.empty and pd.notna(dragon_df.at[0, "Color"]) else "🌸 Sakura Pink"
    except Exception:
        sheet_love = 0
        last_fed = time.time()
        sheet_name = "Baby Dragon"
        sheet_acc = "None"
        sheet_col = "🌸 Sakura Pink"

    if last_fed > 0 and "cached_love" not in st.session_state:
        hours_away = (time.time() - last_fed) / 3600
        decay = int(hours_away // 12)
        sheet_love = max(0, sheet_love - decay)

    love = st.session_state.get("cached_love", sheet_love)
    dragon_name = st.session_state.get("cached_name", sheet_name)
    accessory = st.session_state.get("cached_acc", sheet_acc)
    dragon_color = st.session_state.get("cached_col", sheet_col)

    def update_dragon(new_love, new_name=dragon_name, new_acc=accessory, new_col=dragon_color):
        st.session_state.cached_love = new_love
        st.session_state.cached_name = new_name
        st.session_state.cached_acc = new_acc
        st.session_state.cached_col = new_col
        try:
            new_df = pd.DataFrame([{
                "Love": new_love,
                "LastFed": time.time(),
                "Name": new_name,
                "Accessory": new_acc,
                "Goal": reading_goal,
                "Color": new_col
            }])
            conn.update(worksheet="DragonStats", data=new_df)
        except Exception:
            pass

    if "dragon_msg" not in st.session_state:
        st.session_state.dragon_msg = ""
    if "dragon_action" not in st.session_state:
        st.session_state.dragon_action = ""

    # Determine growth stage
    if love == 0:
        stage_label = "🥚 Sleeping Egg"
    elif love < 6:
        stage_label = "🐣 Tiny Hatchling"
    elif love < 15:
        stage_label = "✨ Playful Juvenile"
    else:
        stage_label = "👑 Majestic Guardian Dragon"

    st.subheader(f"🐉 {dragon_name} — {stage_label}")

    # Color palette dictionary (body, wing, belly, outline)
    palettes = {
        "🌸 Sakura Pink": ("#FFB6C1", "#FF9EBB", "#FFE4EC", "#FF69B4"),
        "💜 Lavender Mist": ("#D8BFD8", "#C39BD3", "#F5EEF8", "#8E44AD"),
        "🩵 Mint Fairy": ("#A3E4D7", "#76D7C4", "#E8F8F5", "#1ABC9C"),
        "🍑 Peach Blossom": ("#FAD7A0", "#F8C471", "#FEF5E7", "#E67E22"),
        "🤍 Pearl White": ("#F8F9F9", "#E5E7E9", "#FFFFFF", "#D98880")
    }
    body_c, wing_c, belly_c, line_c = palettes.get(dragon_color, palettes["🌸 Sakura Pink"])

    # Action overlay graphic (Pet, Berry, or Gem)
    action_svg = ""
    if st.session_state.dragon_action == "pet":
        action_svg = '<text x="35" y="65" font-size="24">💕</text><text x="155" y="60" font-size="22">💖</text><text x="145" y="105" font-size="18">✨</text>'
    elif st.session_state.dragon_action == "berry":
        action_svg = '<text x="32" y="135" font-size="26">🍓</text><text x="152" y="75" font-size="20">😋</text><text x="155" y="135" font-size="22">🍓</text>'
    elif st.session_state.dragon_action == "gem":
        action_svg = '<text x="30" y="135" font-size="26">💎</text><text x="152" y="65" font-size="22">✨</text><text x="152" y="135" font-size="26">💎</text>'

    # Scenic Sanctuary Background (Moon, Stars, Hills & Little Book Stack)
    bg_svg = """
    <defs>
      <linearGradient id="skyGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#FCE4EC"/>
        <stop offset="100%" stop-color="#E1BEE7"/>
      </linearGradient>
    </defs>
    <rect x="0" y="0" width="220" height="200" rx="22" fill="url(#skyGrad)" stroke="#FF69B4" stroke-width="3"/>
    <circle cx="180" cy="36" r="14" fill="#FFF9C4" opacity="0.9"/>
    <circle cx="185" cy="33" r="12" fill="#FCE4EC"/>
    <text x="25" y="35" font-size="12" opacity="0.8">✨</text>
    <text x="135" y="28" font-size="11" opacity="0.8">✨</text>
    <path d="M0 165 Q65 142 120 162 Q175 145 220 160 L220 200 L0 200 Z" fill="#F8BBD0" opacity="0.7"/>
    <path d="M0 175 Q90 158 220 175 L220 200 L0 200 Z" fill="#F48FB1" opacity="0.55"/>
    <rect x="18" y="168" width="34" height="8" rx="2" fill="#CE93D8" stroke="#8E24AA" stroke-width="1.5"/>
    <rect x="21" y="160" width="30" height="8" rx="2" fill="#F48FB1" stroke="#C2185B" stroke-width="1.5"/>
    """

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
        if love < 6:
            scale = "0.86"
            wings = f'<path d="M68 108 Q42 88 55 120 Q48 130 70 126 Z" fill="{wing_c}" stroke="{line_c}" stroke-width="3"/><path d="M152 108 Q178 88 165 120 Q172 130 150 126 Z" fill="{wing_c}" stroke="{line_c}" stroke-width="3"/>'
        elif love < 15:
            scale = "0.96"
            wings = f'<path d="M66 105 Q24 68 44 122 Q34 138 68 132 Z" fill="{wing_c}" stroke="{line_c}" stroke-width="3"/><path d="M154 105 Q196 68 176 122 Q186 138 152 132 Z" fill="{wing_c}" stroke="{line_c}" stroke-width="3"/>'
        else:
            scale = "1.04"
            wings = f'<path d="M65 102 Q12 52 36 124 Q24 144 68 134 Z" fill="{wing_c}" stroke="{line_c}" stroke-width="3.5"/><path d="M155 102 Q208 52 184 124 Q196 144 152 134 Z" fill="{wing_c}" stroke="{line_c}" stroke-width="3.5"/>'

        acc_svg = ""
        if accessory == "👑 Royal Crown" or (accessory == "None" and love >= 15):
            acc_svg = '<polygon points="92,42 100,25 110,38 120,25 128,42" fill="#FFD700" stroke="#E6AC00" stroke-width="2"/>'
        elif accessory == "🌸 Flower Crown":
            acc_svg = '<circle cx="92" cy="44" r="7" fill="#FF69B4"/><circle cx="110" cy="41" r="8" fill="#FFB6C1"/><circle cx="128" cy="44" r="7" fill="#FF69B4"/><circle cx="110" cy="41" r="3" fill="#FFD700"/>'
        elif accessory == "👓 Reading Glasses":
            acc_svg = '<circle cx="96" cy="78" r="10" fill="none" stroke="#4A2545" stroke-width="2.5"/><circle cx="124" cy="78" r="10" fill="none" stroke="#4A2545" stroke-width="2.5"/><line x1="106" y1="78" x2="114" y2="78" stroke="#4A2545" stroke-width="2.5"/>'

        dragon_svg = f"""
        <style>
        @keyframes dragonBounce {{
            0%, 100% {{ transform: translateY(0px) scale({scale}); }}
            50% {{ transform: translateY(-6px) scale({scale}); }}
        }}
        .baby-dragon {{ transform-origin: 110px 130px; animation: dragonBounce 2.2s ease-in-out infinite; }}
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
              {acc_svg}
              <path d="M90 80 Q96 72 102 80" fill="none" stroke="#4A2545" stroke-width="3.5" stroke-linecap="round"/>
              <path d="M118 80 Q124 72 130 80" fill="none" stroke="#4A2545" stroke-width="3.5" stroke-linecap="round"/>
              <ellipse cx="85" cy="90" rx="7" ry="4" fill="#FF69B4" opacity="0.6"/>
              <ellipse cx="135" cy="90" rx="7" ry="4" fill="#FF69B4" opacity="0.6"/>
              <path d="M103 93 Q110 100 117 93" fill="none" stroke="#4A2545" stroke-width="3" stroke-linecap="round"/>
            </g>
            {action_svg}
          </svg>
        </div>
        """

    dragon_svg = "\n".join(line.strip() for line in dragon_svg.splitlines())
    st.markdown(dragon_svg, unsafe_allow_html=True)

    if love == 0:
        mood = f"😴 {dragon_name} is fast asleep in her egg (Tap below to hatch her!)"
    elif love < 6:
        mood = f"🐣 {dragon_name} is a tiny hatchling waddling around your books"
    elif love < 15:
        mood = f"✨ {dragon_name} is growing bigger wings and blowing heart-shaped smoke rings"
    else:
        mood = f"👑 {dragon_name} is a full-grown Majestic Guardian watching over your hoard!"

    st.write(f"**Current Mood:** {mood}")
    st.progress(min(love / 15, 1.0), text=f"Dragon Affection: {love} 💖")

    dragon_reactions = [
        f"{dragon_name} chirps softly and curls her tail around your wrist! 💕🐉",
        f"{dragon_name} sneezes a tiny puff of rose-gold glitter onto your book! ✨🌸",
        f"{dragon_name} rolls over for belly rubs and purrs like a tiny motor! 💖🥚",
        f"{dragon_name} puffs out her chest proudly to guard your favorite books! 📚🐉"
    ]

    d_col1, d_col2, d_col3 = st.columns(3)
    with d_col1:
        if st.button("🥚 Pet Dragon", use_container_width=True):
            new_score = love + 1
            update_dragon(new_score)
            st.session_state.dragon_msg = random.choice(dragon_reactions)
            st.session_state.dragon_action = "pet"
            if new_score in (6, 15):
                st.balloons()
            st.rerun()
    with d_col2:
        if st.button("🍓 Feed Berry", use_container_width=True):
            new_score = love + 2
            update_dragon(new_score)
            st.session_state.dragon_msg = f"Nom nom! {dragon_name} gobbles the sweet berry and does a happy spin! 🍓🐉"
            st.session_state.dragon_action = "berry"
            if (new_score >= 6 and love < 6) or (new_score >= 15 and love < 15):
                st.balloons()
            st.rerun()
    with d_col3:
        if st.button("💎 Shiny Gem", use_container_width=True):
            new_score = love + 3
            update_dragon(new_score)
            st.session_state.dragon_msg = f"Ooooh! {dragon_name} adds the sparkling gem to her treasure hoard! 💎✨"
            st.session_state.dragon_action = "gem"
            if (new_score >= 6 and love < 6) or (new_score >= 15 and love < 15):
                st.balloons()
            st.rerun()

    if st.session_state.dragon_msg:
        st.info(st.session_state.dragon_msg)

    # --- Dragon Name, Color & Accessory Closet ---
    auto_open_naming = (love > 0 and dragon_name == "Baby Dragon")
    with st.expander(f"🎀 Customize {dragon_name} (Name, Color & Accessories)", expanded=auto_open_naming):
        new_dragon_name = st.text_input("Give your dragon a name:", value="" if dragon_name == "Baby Dragon" else dragon_name, placeholder="Type a name...")

        color_options = ["🌸 Sakura Pink", "💜 Lavender Mist", "🩵 Mint Fairy", "🍑 Peach Blossom", "🤍 Pearl White"]
        current_col_idx = color_options.index(dragon_color) if dragon_color in color_options else 0
        chosen_color = st.selectbox("Scale Color:", color_options, index=current_col_idx)

        acc_options = ["None", "🌸 Flower Crown", "👓 Reading Glasses", "👑 Royal Crown"]
        current_acc_idx = acc_options.index(accessory) if accessory in acc_options else 0
        chosen_acc = st.selectbox("Equip Accessory (Unlocks at 3+ Affection)", acc_options, index=current_acc_idx)

        if st.button("Save Dragon Look ✨", use_container_width=True):
            if chosen_acc != "None" and love < 3:
                st.warning("Pet or feed your dragon to reach 3+ Affection first to unlock accessories! 🥚")
            else:
                st.session_state.dragon_action = ""
                update_dragon(
                    love,
                    new_name=new_dragon_name.strip() or "Baby Dragon",
                    new_acc=chosen_acc,
                    new_col=chosen_color
                )
                st.success(f"Updated {new_dragon_name.strip() or 'Baby Dragon'}!")
                st.rerun()
