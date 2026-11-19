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
    if "Goal" in goal_df.columns and not goal_df.empty and pd.notna(goal_df.at[0, "Goal"]):
        reading_goal = int(float(goal_df.at[0, "Goal"]))
    else:
        reading_goal = 20
except Exception:
    goal_df = pd.DataFrame([{"Goal": 20}])
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
            goal_df = pd.DataFrame([{"Goal": int(new_goal)}])
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
                c_df = conn.read(worksheet="Coupons", ttl=0)
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
        dragon_df = conn.read(worksheet="DragonStats", ttl=0)
        saved_love = int(float(dragon_df.at[0, "Love"])) if "Love" in dragon_df.columns and not dragon_df.empty and pd.notna(dragon_df.at[0, "Love"]) else 0
        last_fed = float(dragon_df.at[0, "LastFed"]) if "LastFed" in dragon_df.columns and not dragon_df.empty and pd.notna(dragon_df.at[0, "LastFed"]) else time.time()
        dragon_name = str(dragon_df.at[0, "Name"]) if "Name" in dragon_df.columns and not dragon_df.empty and pd.notna(dragon_df.at[0, "Name"]) else "Baby Dragon"
        accessory = str(dragon_df.at[0, "Accessory"]) if "Accessory" in dragon_df.columns and not dragon_df.empty and pd.notna(dragon_df.at[0, "Accessory"]) else "None"
        saved_goal = int(float(dragon_df.at[0, "Goal"])) if "Goal" in dragon_df.columns and not dragon_df.empty and pd.notna(dragon_df.at[0, "Goal"]) else 20
    except Exception:
        saved_love = 0
        last_fed = time.time()
        dragon_name = "Baby Dragon"
        accessory = "None"
        saved_goal = 20

    if last_fed > 0:
        hours_away = (time.time() - last_fed) / 3600
        decay = int(hours_away // 12)
        love = max(0, saved_love - decay)
    else:
        love = saved_love

    def update_dragon(new_love, new_name=dragon_name, new_acc=accessory):
        new_df = pd.DataFrame([{
            "Love": new_love,
            "LastFed": time.time(),
            "Name": new_name,
            "Accessory": new_acc,
            "Goal": saved_goal
        }])
        conn.update(worksheet="DragonStats", data=new_df)
        st.cache_data.clear()

    st.subheader(f"🐉 {dragon_name} — Your Guardian Dragon")

    # --- Cute Animated Pink Baby Dragon SVG with Accessories ---
    if love == 0:
        dragon_svg = """
        <div style="text-align:center; margin: 10px 0;">
          <svg width="150" height="150" viewBox="0 0 200 200">
            <ellipse cx="100" cy="115" rx="52" ry="65" fill="#FFD1DC" stroke="#FF69B4" stroke-width="4"/>
            <path d="M52 105 L75 92 L95 108 L115 90 L135 106 L148 98" fill="none" stroke="#FF69B4" stroke-width="4" stroke-linecap="round"/>
            <circle cx="80" cy="135" r="7" fill="#FF9EBB"/>
            <circle cx="122" cy="80" r="5" fill="#FF9EBB"/>
            <text x="135" y="55" font-size="22" fill="#9C1B5B">💤</text>
          </svg>
        </div>
        """
    else:
        acc_svg = ""
        if accessory == "👑 Royal Crown" or (accessory == "None" and love >= 15):
            acc_svg = '<polygon points="82,42 90,25 100,38 110,25 118,42" fill="#FFD700" stroke="#E6AC00" stroke-width="2"/>'
        elif accessory == "🌸 Flower Crown":
            acc_svg = '<circle cx="82" cy="44" r="7" fill="#FF69B4"/><circle cx="100" cy="41" r="8" fill="#FFB6C1"/><circle cx="118" cy="44" r="7" fill="#FF69B4"/><circle cx="100" cy="41" r="3" fill="#FFD700"/>'
        elif accessory == "👓 Reading Glasses":
            acc_svg = '<circle cx="86" cy="78" r="10" fill="none" stroke="#4A2545" stroke-width="2.5"/><circle cx="114" cy="78" r="10" fill="none" stroke="#4A2545" stroke-width="2.5"/><line x1="96" y1="78" x2="104" y2="78" stroke="#4A2545" stroke-width="2.5"/>'

        hearts = '<text x="142" y="55" font-size="20">💖</text><text x="38" y="65" font-size="18">✨</text>' if love >= 5 else ''
        dragon_svg = f"""
        <style>
        @keyframes dragonBounce {{
            0%, 100% {{ transform: translateY(0px); }}
            50% {{ transform: translateY(-7px); }}
        }}
        .baby-dragon {{ animation: dragonBounce 2.2s ease-in-out infinite; }}
        </style>
        <div style="text-align:center; margin: 10px 0;">
          <svg class="baby-dragon" width="165" height="165" viewBox="0 0 200 200">
            <path d="M55 105 Q20 75 40 120 Q30 135 58 130 Z" fill="#FF9EBB" stroke="#FF69B4" stroke-width="3"/>
            <path d="M145 105 Q180 75 160 120 Q170 135 142 130 Z" fill="#FF9EBB" stroke="#FF69B4" stroke-width="3"/>
            <path d="M135 155 Q175 155 170 130 Q165 120 155 130" fill="none" stroke="#FF69B4" stroke-width="8" stroke-linecap="round"/>
            <ellipse cx="100" cy="135" rx="42" ry="45" fill="#FFB6C1" stroke="#FF69B4" stroke-width="3.5"/>
            <ellipse cx="100" cy="140" rx="26" ry="30" fill="#FFE4EC"/>
            <circle cx="100" cy="82" r="38" fill="#FFB6C1" stroke="#FF69B4" stroke-width="3.5"/>
            <polygon points="75,52 68,32 86,46" fill="#FFF0F5" stroke="#FF69B4" stroke-width="3"/>
            <polygon points="125,52 132,32 114,46" fill="#FFF0F5" stroke="#FF69B4" stroke-width="3"/>
            {acc_svg}
            <path d="M80 80 Q86 72 92 80" fill="none" stroke="#4A2545" stroke-width="3.5" stroke-linecap="round"/>
            <path d="M108 80 Q114 72 120 80" fill="none" stroke="#4A2545" stroke-width="3.5" stroke-linecap="round"/>
            <ellipse cx="75" cy="90" rx="7" ry="4" fill="#FF69B4" opacity="0.6"/>
            <ellipse cx="125" cy="90" rx="7" ry="4" fill="#FF69B4" opacity="0.6"/>
            <path d="M93 93 Q100 100 107 93" fill="none" stroke="#4A2545" stroke-width="3" stroke-linecap="round"/>
            {hearts}
          </svg>
        </div>
        """
    dragon_svg = "\n".join(line.strip() for line in dragon_svg.splitlines())
    st.markdown(dragon_svg, unsafe_allow_html=True)

    if love == 0:
        mood = f"😴 {dragon_name} is fast asleep in his egg (Tap below to wake him up!)"
    elif love < 5:
        mood = f"🌸 {dragon_name} is curled up and purring happily"
    elif love < 10:
        mood = f"✨ {dragon_name} is blowing tiny heart-shaped smoke rings"
    elif love < 15:
        mood = f"💖 {dragon_name} is doing happy wing flaps around your shelves"
    else:
        mood = f" 👑 {dragon_name} is the Supreme Guardian of the Book Hoard!"

    st.write(f"**Current Mood:** {mood}")
    st.progress(min(love / 15, 1.0), text=f"Dragon Affection: {love} 💖")
    
    dragon_reactions = [
        f"{dragon_name} chirps softly and curls his tail around your wrist! 💕🐉",
        f"{dragon_name} sneezes a tiny puff of rose-gold glitter onto your book! ✨🌸",
        f"{dragon_name} rolls over for belly rubs and purrs like a tiny motor! 💖🥚",
        f"{dragon_name} puffs out his chest proudly to guard your favorite books! 📚🐉",
        f"A tiny heart-shaped smoke ring floats up from {dragon_name}'s nose! 💕💨"
    ]
    
    if "dragon_msg" not in st.session_state:
        st.session_state.dragon_msg = ""
        
    d_col1, d_col2, d_col3 = st.columns(3)
     with d_col1:
         if st.button("🥚 Pet Dragon", use_container_width=True):
             new_score = love + 1 update_dragon(new_score)
             st.session_state.dragon_msg = random.choice(dragon_reactions)
             if new_score == 15:
                 st.balloons()
            st.rerun(
    with d_col2:
        if st.button("🍓 Feed Berry", use_container_width=True):
            new_score = love + 2
            update_dragon(new_score)
            st.session_state.dragon_msg = f"Nom nom! {dragon_name} gobbles the sweet berry and does a happy spin! 🍓🐉"
            if new_score >= 15:
                st.balloons()
            st.rerun()
    with d_col3:
        if st.button("💎 Shiny Gem", use_container_width=True):
            new_score = love + 3
            update_dragon(new_score)
            st.session_state.dragon_msg = f"Ooooh! {dragon_name} adds the pink gem to his treasure hoard! 💎✨"
            if new_score >= 15:
                st.balloons()
            st.rerun()
            
    if st.session_state.dragon_msg:
        st.info(st.session_state.dragon_msg)

# --- Dragon Name & Accessory Closet ---
auto_open_naming = (love > 0 and dragon_name == "Baby Dragon")
with st.expander(f"🎀 Customize {dragon_name} (Name & Accessories)", expanded=auto_open_naming):
    new_dragon_name = st.text_input("Give your dragon a name:", value="" if dragon_name == "Baby Dragon" else dragon_name, placeholder="Type a name...")
    acc_options = ["None", "🌸 Flower Crown", "👓 Reading Glasses", "👑 Royal Crown"]
    current_acc_idx = acc_options.index(accessory) if accessory in acc_options else 0
    chosen_acc = st.selectbox("Equip Accessory (Unlocks at 3+ Affection)", acc_options, index=current_acc_idx)

    if st.button("Save Dragon Look ✨", use_container_width=True):
        if chosen_acc != "None" and love < 3:
            st.warning("Pet or feed your dragon to reach 3+ Affection first to unlock accessories! 🥚")
        else:
            update_dragon(love, new_name=new_dragon_name.strip() or "Baby Dragon", new_acc=chosen_acc)
            st.success(f"Updated {new_dragon_name.strip() or 'Baby Dragon'}!")
            st.rerun()

