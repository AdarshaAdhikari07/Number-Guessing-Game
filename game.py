# game.py
import streamlit as st
import random
import json
import os
from datetime import datetime

# ============ CONFIGURATION ============
LEADERBOARD_FILE = "leaderboard.json"
MAX_LEADERBOARD_ENTRIES = 10

# ============ INITIALIZE SESSION STATE ============
if 'game_state' not in st.session_state:
    st.session_state.game_state = 'menu'  # menu, playing, game_over
    st.session_state.target_number = 0
    st.session_state.guesses = []
    st.session_state.difficulty = 'medium'
    st.session_state.max_attempts = 10
    st.session_state.score = 0
    st.session_state.player_name = ""
    st.session_state.start_time = None
    st.session_state.elapsed_time = 0

# ============ PAGE CONFIG ============
st.set_page_config(
    page_title="🎮 Number Guess Game",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============ CUSTOM CSS ============
st.markdown("""
<style>
    .main-title {
        text-align: center;
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 20px;
        animation: pulse 2s infinite;
    }
    
    .game-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 10px 0;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    .score-board {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 15px;
        border-radius: 10px;
        color: white;
        text-align: center;
        font-weight: bold;
        box-shadow: 0 4px 15px rgba(245, 87, 108, 0.4);
    }
    
    .leaderboard-entry {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 12px;
        margin: 8px 0;
        border-radius: 8px;
        color: white;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .medal {
        font-size: 1.5rem;
        margin-right: 10px;
    }
    
    .win-message {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        font-weight: bold;
    }
    
    .lose-message {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        font-weight: bold;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
</style>
""", unsafe_allow_html=True)

# ============ LEADERBOARD FUNCTIONS ============
def load_leaderboard():
    """Load leaderboard from JSON file"""
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_leaderboard(leaderboard):
    """Save leaderboard to JSON file"""
    with open(LEADERBOARD_FILE, 'w') as f:
        json.dump(leaderboard, f, indent=2)

def add_score(player_name, score, difficulty, time_taken):
    """Add a new score to leaderboard"""
    leaderboard = load_leaderboard()
    
    new_entry = {
        "rank": len(leaderboard) + 1,
        "name": player_name,
        "score": score,
        "difficulty": difficulty,
        "time": time_taken,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    leaderboard.append(new_entry)
    leaderboard.sort(key=lambda x: x['score'], reverse=True)
    
    # Keep only top entries
    leaderboard = leaderboard[:MAX_LEADERBOARD_ENTRIES]
    
    # Update ranks
    for i, entry in enumerate(leaderboard, 1):
        entry['rank'] = i
    
    save_leaderboard(leaderboard)

def display_leaderboard():
    """Display top scores"""
    leaderboard = load_leaderboard()
    
    if not leaderboard:
        st.info("📊 No scores yet! Be the first to play!")
        return
    
    st.write("### 🏆 Top Scores")
    
    medals = ["🥇", "🥈", "🥉"]
    
    for entry in leaderboard:
        medal = medals[entry['rank'] - 1] if entry['rank'] <= 3 else f"#{entry['rank']}"
        
        col1, col2, col3, col4, col5 = st.columns([1, 2, 1, 1, 1])
        
        with col1:
            st.write(medal)
        with col2:
            st.write(f"**{entry['name']}**")
        with col3:
            st.write(f"**{entry['score']}** pts")
        with col4:
            st.write(f"🎯 {entry['difficulty']}")
        with col5:
            st.write(f"⏱️ {entry['time']}s")

# ============ GAME FUNCTIONS ============
def reset_game():
    """Reset game to initial state"""
    st.session_state.game_state = 'menu'
    st.session_state.guesses = []
    st.session_state.score = 0
    st.session_state.start_time = None
    st.session_state.elapsed_time = 0

def start_game(difficulty):
    """Start a new game with selected difficulty"""
    st.session_state.difficulty = difficulty
    
    if difficulty == 'easy':
        st.session_state.target_number = random.randint(1, 50)
        st.session_state.max_attempts = 15
    elif difficulty == 'medium':
        st.session_state.target_number = random.randint(1, 100)
        st.session_state.max_attempts = 10
    elif difficulty == 'hard':
        st.session_state.target_number = random.randint(1, 500)
        st.session_state.max_attempts = 8
    
    st.session_state.game_state = 'playing'
    st.session_state.guesses = []
    
    import time
    st.session_state.start_time = time.time()

def check_guess(guess):
    """Check the player's guess"""
    try:
        guess_num = int(guess)
        
        # Validate range
        max_range = 50 if st.session_state.difficulty == 'easy' else \
                   100 if st.session_state.difficulty == 'medium' else 500
        
        if guess_num < 1 or guess_num > max_range:
            st.warning(f"❌ Please enter a number between 1 and {max_range}!")
            return
        
        # Check if already guessed
        if guess_num in st.session_state.guesses:
            st.warning(f"⚠️ You already guessed {guess_num}!")
            return
        
        st.session_state.guesses.append(guess_num)
        
        # Check if correct
        if guess_num == st.session_state.target_number:
            st.session_state.game_state = 'game_over'
            # Calculate score based on attempts
            attempts_left = st.session_state.max_attempts - len(st.session_state.guesses) + 1
            difficulty_multiplier = {'easy': 1, 'medium': 2, 'hard': 3}
            st.session_state.score = max(0, attempts_left * 100 * difficulty_multiplier[st.session_state.difficulty])
            
            import time
            st.session_state.elapsed_time = int(time.time() - st.session_state.start_time)
        
        # Check if out of attempts
        elif len(st.session_state.guesses) >= st.session_state.max_attempts:
            st.session_state.game_state = 'game_over'
            st.session_state.score = 0
            
            import time
            st.session_state.elapsed_time = int(time.time() - st.session_state.start_time)
    
    except ValueError:
        st.warning("❌ Please enter a valid number!")

def get_difficulty_color(difficulty):
    """Get color based on difficulty"""
    colors = {
        'easy': '🟢',
        'medium': '🟡',
        'hard': '🔴'
    }
    return colors.get(difficulty, '⚪')

# ============ MAIN UI ============
st.markdown('<h1 class="main-title">🎮 Number Guessing Game</h1>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("---")
    st.write("### 📊 Game Statistics")
    
    leaderboard = load_leaderboard()
    if leaderboard:
        st.metric("Total Games", len(leaderboard))
        st.metric("Top Score", f"{leaderboard[0]['score']} pts")
    else:
        st.info("No games played yet!")
    
    st.markdown("---")
    st.write("### 📖 How to Play:")
    st.info("""
    1. Enter your name
    2. Select difficulty level
    3. Computer picks a random number
    4. Guess the number in limited attempts
    5. Get feedback: ⬆️ too low, ⬇️ too high
    6. Win and climb the leaderboard!
    """)
    
    st.markdown("---")
    st.write("### 🎯 Scoring System:")
    st.write("""
    - **Easy**: 1x multiplier
    - **Medium**: 2x multiplier
    - **Hard**: 3x multiplier
    
    Base points: (Attempts Left × 100)
    """)

# ============ MENU SCREEN ============
if st.session_state.game_state == 'menu':
    col1, col2, col3 = st.columns(3)
    
    st.write("---")
    
    # Player name input
    st.write("### 👤 Enter Your Name:")
    player_name = st.text_input("Your name:", value=st.session_state.player_name, label_visibility="collapsed")
    st.session_state.player_name = player_name
    
    st.write("---")
    st.write("### 🎮 Select Difficulty Level:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🟢 Easy\n(1-50, 15 tries)", use_container_width=True, key="easy_btn"):
            if player_name.strip():
                start_game('easy')
                st.rerun()
            else:
                st.warning("Please enter your name first!")
    
    with col2:
        if st.button("🟡 Medium\n(1-100, 10 tries)", use_container_width=True, key="medium_btn"):
            if player_name.strip():
                start_game('medium')
                st.rerun()
            else:
                st.warning("Please enter your name first!")
    
    with col3:
        if st.button("🔴 Hard\n(1-500, 8 tries)", use_container_width=True, key="hard_btn"):
            if player_name.strip():
                start_game('hard')
                st.rerun()
            else:
                st.warning("Please enter your name first!")
    
    # Leaderboard section
    st.write("---")
    display_leaderboard()

# ============ PLAYING SCREEN ============
elif st.session_state.game_state == 'playing':
    import time
    
    # Sidebar with game info
    with st.sidebar:
        st.write("### 📊 Game Info")
        st.markdown(f'<div class="score-board">👤 Player: {st.session_state.player_name}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="score-board">🎯 Difficulty: {st.session_state.difficulty.upper()}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="score-board">❤️ Attempts Left: {st.session_state.max_attempts - len(st.session_state.guesses)}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="score-board">📍 Guesses Made: {len(st.session_state.guesses)}</div>', unsafe_allow_html=True)
        
        # Timer
        elapsed = int(time.time() - st.session_state.start_time)
        st.markdown(f'<div class="score-board">⏱️ Time: {elapsed}s</div>', unsafe_allow_html=True)
        
        if st.session_state.guesses:
            st.write("---")
            st.write("**📝 Previous Guesses:**")
            guesses_str = ", ".join(map(str, st.session_state.guesses))
            st.write(guesses_str)
    
    # Main game area
    max_range = 50 if st.session_state.difficulty == 'easy' else \
               100 if st.session_state.difficulty == 'medium' else 500
    
    st.markdown(f"""
    <div class="game-card">
        <h2>🎯 Guess the Number!</h2>
        <h3>{1} - {max_range}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        guess_input = st.number_input(
            "Enter your guess:",
            min_value=1,
            max_value=max_range,
            value=max_range // 2,
            step=1,
            label_visibility="collapsed"
        )
    
    with col2:
        if st.button("🎯 Guess!", use_container_width=True, key="guess_btn"):
            check_guess(guess_input)
            st.rerun()
    
    # Show feedback on previous guesses
    if st.session_state.guesses:
        st.write("---")
        st.write("### 💡 Feedback:")
        last_guess = st.session_state.guesses[-1]
        
        if last_guess < st.session_state.target_number:
            st.success(f"📈 {last_guess} is too LOW! Try a higher number.")
        elif last_guess > st.session_state.target_number:
            st.error(f"📉 {last_guess} is too HIGH! Try a lower number.")
        else:
            st.success(f"🎉 {last_guess} is CORRECT!")

# ============ GAME OVER SCREEN ============
elif st.session_state.game_state == 'game_over':
    if st.session_state.guesses and st.session_state.guesses[-1] == st.session_state.target_number:
        # WIN STATE
        st.markdown(
            f'<div class="win-message"><h1>🎉 CONGRATULATIONS!</h1><h2>You Won!</h2></div>',
            unsafe_allow_html=True
        )
        st.balloons()
        
        st.write("---")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🎯 Target", st.session_state.target_number)
        with col2:
            st.metric("📍 Guesses", len(st.session_state.guesses))
        with col3:
            st.metric("⭐ Points", st.session_state.score)
        with col4:
            st.metric("⏱️ Time", f"{st.session_state.elapsed_time}s")
        
        st.write("---")
        st.write("**📝 Your guesses were:**")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        for i, guess in enumerate(st.session_state.guesses):
            with [col1, col2, col3, col4, col5][i % 5]:
                st.write(f"🔹 {guess}")
        
        st.write("---")
        
        # Save score
        add_score(
            st.session_state.player_name,
            st.session_state.score,
            st.session_state.difficulty,
            st.session_state.elapsed_time
        )
        
        st.success(f"✅ Score saved to leaderboard!")
    
    else:
        # LOSE STATE
        st.markdown(
            f'<div class="lose-message"><h1>😢 Game Over!</h1><h2>You didn\'t guess the number in time.</h2></div>',
            unsafe_allow_html=True
        )
        
        st.write("---")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🎯 The Answer", st.session_state.target_number)
        with col2:
            st.metric("📍 Your Guesses", len(st.session_state.guesses))
        with col3:
            st.metric("⭐ Points", 0)
        with col4:
            st.metric("⏱️ Time", f"{st.session_state.elapsed_time}s")
        
        st.write("---")
        st.write("**📝 Your guesses were:**")
        st.write(", ".join(map(str, st.session_state.guesses)))
    
    st.write("---")
    st.write("### 🎮 Play Again?")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Play Again", use_container_width=True, key="play_again"):
            reset_game()
            st.rerun()
    
    with col2:
        if st.button("📊 View Leaderboard", use_container_width=True, key="view_leaderboard"):
            reset_game()
            st.session_state.game_state = 'menu'
            st.rerun()
    
    with col3:
        if st.button("🏠 Back to Menu", use_container_width=True, key="menu"):
            reset_game()
            st.rerun()
