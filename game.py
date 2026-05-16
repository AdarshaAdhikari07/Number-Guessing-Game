# game.py
import streamlit as st
import random
import json
import os
from datetime import datetime
import base64
from pathlib import Path

# ============ CONFIGURATION ============
LEADERBOARD_FILE = "leaderboard.json"
MAX_LEADERBOARD_ENTRIES = 10

# ============ AUDIO GENERATION FUNCTIONS ============
def generate_beep_sound(frequency=1000, duration=0.2):
    """Generate a beep sound using numpy"""
    import numpy as np
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration))
    wave = np.sin(2 * np.pi * frequency * t)
    # Normalize to 16-bit audio
    audio_data = (wave * 32767).astype(np.int16)
    return audio_data

def generate_success_sound():
    """Generate a success/winning sound"""
    import numpy as np
    sample_rate = 44100
    duration = 0.5
    
    frequencies = [523.25, 659.25, 783.99]  # C, E, G
    audio = np.array([])
    
    for freq in frequencies:
        t = np.linspace(0, duration / 3, int(sample_rate * duration / 3))
        wave = np.sin(2 * np.pi * freq * t)
        # Add envelope
        envelope = np.linspace(1, 0, len(wave))
        wave = wave * envelope
        audio = np.concatenate([audio, wave])
    
    audio_data = (audio * 32767).astype(np.int16)
    return audio_data

def generate_failure_sound():
    """Generate a failure/wrong sound"""
    import numpy as np
    sample_rate = 44100
    duration = 0.4
    
    frequencies = [349.23, 293.66]  # F, D
    audio = np.array([])
    
    for freq in frequencies:
        t = np.linspace(0, duration / 2, int(sample_rate * duration / 2))
        wave = np.sin(2 * np.pi * freq * t)
        envelope = np.linspace(1, 0, len(wave))
        wave = wave * envelope
        audio = np.concatenate([audio, wave])
    
    audio_data = (audio * 32767).astype(np.int16)
    return audio_data

def generate_click_sound():
    """Generate a click/tap sound"""
    import numpy as np
    sample_rate = 44100
    duration = 0.1
    
    t = np.linspace(0, duration, int(sample_rate * duration))
    # Create a short click sound
    wave = np.sin(2 * np.pi * 800 * t)
    envelope = np.exp(-5 * t)
    wave = wave * envelope
    
    audio_data = (wave * 32767).astype(np.int16)
    return audio_data

def audio_to_html(audio_data, autoplay=False):
    """Convert audio data to HTML audio element"""
    import numpy as np
    from scipy import signal
    import io
    import wave
    
    sample_rate = 44100
    
    # Create WAV file in memory
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())
    
    wav_buffer.seek(0)
    audio_bytes = wav_buffer.read()
    audio_b64 = base64.b64encode(audio_bytes).decode()
    
    autoplay_attr = "autoplay" if autoplay else ""
    html = f'''
        <audio {autoplay_attr} controls style="width: 100%; height: 40px;">
            <source src="data:audio/wav;base64,{audio_b64}" type="audio/wav">
            Your browser does not support the audio element.
        </audio>
    '''
    return html

# ============ INITIALIZE SESSION STATE ============
if 'game_state' not in st.session_state:
    st.session_state.game_state = 'menu'
    st.session_state.target_number = 0
    st.session_state.guesses = []
    st.session_state.difficulty = 'medium'
    st.session_state.max_attempts = 10
    st.session_state.score = 0
    st.session_state.start_time = None
    st.session_state.elapsed_time = 0
    st.session_state.sound_enabled = True
    st.session_state.combo = 0
    st.session_state.perfect_game = False

# ============ PAGE CONFIG ============
st.set_page_config(
    page_title="🎮 Number Guess Game",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============ CUSTOM CSS WITH ANIMATIONS ============
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@300;400;600;700&display=swap');
    
    * {
        font-family: 'Fredoka', sans-serif;
    }
    
    .main-title {
        text-align: center;
        font-size: 3.5rem;
        font-weight: 700;
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4, #FFE66D);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 20px;
        animation: titlePulse 3s ease-in-out infinite;
        letter-spacing: 2px;
    }
    
    .game-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 30px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin: 15px 0;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.5);
        border: 3px solid rgba(255, 255, 255, 0.2);
    }
    
    .score-board {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 18px;
        border-radius: 12px;
        color: white;
        text-align: center;
        font-weight: bold;
        font-size: 1.1rem;
        box-shadow: 0 8px 25px rgba(245, 87, 108, 0.5);
        border: 3px solid rgba(255, 255, 255, 0.2);
        margin: 10px 0;
    }
    
    .difficulty-btn {
        font-size: 1.2rem;
        font-weight: 600;
        padding: 20px;
        border-radius: 12px;
        transition: all 0.3s ease;
    }
    
    .leaderboard-entry {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 15px;
        margin: 12px 0;
        border-radius: 10px;
        color: white;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        border-left: 5px solid #FFE66D;
        animation: slideIn 0.5s ease-out;
    }
    
    .medal {
        font-size: 2rem;
        margin-right: 15px;
    }
    
    .win-message {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 30px;
        border-radius: 15px;
        color: white;
        text-align: center;
        font-weight: bold;
        font-size: 1.5rem;
        box-shadow: 0 8px 25px rgba(56, 239, 125, 0.5);
        border: 3px solid rgba(255, 255, 255, 0.3);
        animation: bounceIn 0.8s ease-out;
    }
    
    .lose-message {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
        padding: 30px;
        border-radius: 15px;
        color: white;
        text-align: center;
        font-weight: bold;
        font-size: 1.5rem;
        box-shadow: 0 8px 25px rgba(255, 107, 107, 0.5);
        border: 3px solid rgba(255, 255, 255, 0.3);
        animation: shake 0.5s ease-out;
    }
    
    .combo-counter {
        background: linear-gradient(135deg, #FFE66D 0%, #FF6B6B 100%);
        padding: 15px;
        border-radius: 10px;
        color: white;
        text-align: center;
        font-weight: bold;
        font-size: 1.3rem;
        box-shadow: 0 4px 15px rgba(255, 230, 109, 0.6);
        animation: pulse 1s ease-in-out infinite;
    }
    
    .feedback-good {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        font-weight: bold;
        margin: 15px 0;
        box-shadow: 0 4px 15px rgba(56, 239, 125, 0.4);
        animation: slideInRight 0.5s ease-out;
    }
    
    .feedback-bad {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        font-weight: bold;
        margin: 15px 0;
        box-shadow: 0 4px 15px rgba(255, 107, 107, 0.4);
        animation: slideInRight 0.5s ease-out;
    }
    
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 10px 0;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        border: 2px solid rgba(255, 255, 255, 0.2);
    }
    
    .progress-bar {
        background: rgba(255, 255, 255, 0.2);
        height: 10px;
        border-radius: 10px;
        overflow: hidden;
        margin: 10px 0;
    }
    
    .progress-fill {
        background: linear-gradient(90deg, #38ef7d 0%, #11998e 100%);
        height: 100%;
        animation: fillProgress 0.6s ease-out;
    }
    
    @keyframes titlePulse {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.05); opacity: 0.8; }
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.1); opacity: 0.9; }
    }
    
    @keyframes bounceIn {
        0% { transform: scale(0.3); opacity: 0; }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); opacity: 1; }
    }
    
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        10%, 30%, 50%, 70%, 90% { transform: translateX(-10px); }
        20%, 40%, 60%, 80% { transform: translateX(10px); }
    }
    
    @keyframes slideIn {
        0% { transform: translateX(-100%); opacity: 0; }
        100% { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideInRight {
        0% { transform: translateX(100%); opacity: 0; }
        100% { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes fillProgress {
        0% { width: 0%; }
        100% { width: 100%; }
    }
    
    .emoji-rain {
        font-size: 3rem;
        animation: fall 3s linear forwards;
    }
    
    @keyframes fall {
        0% { transform: translateY(-100vh) rotate(0deg); opacity: 1; }
        100% { transform: translateY(100vh) rotate(360deg); opacity: 0; }
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

def add_score(score, difficulty, time_taken, guesses_count, perfect):
    """Add a new score to leaderboard"""
    leaderboard = load_leaderboard()
    
    new_entry = {
        "rank": len(leaderboard) + 1,
        "score": score,
        "difficulty": difficulty,
        "time": time_taken,
        "guesses": guesses_count,
        "perfect": perfect,
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
    """Display top scores with animations"""
    leaderboard = load_leaderboard()
    
    if not leaderboard:
        st.info("📊 No scores yet! Be the first to play!")
        return
    
    st.write("### 🏆 Top Scores")
    
    medals = ["🥇", "🥈", "🥉"]
    
    for entry in leaderboard:
        medal = medals[entry['rank'] - 1] if entry['rank'] <= 3 else f"#{entry['rank']}"
        perfect_badge = "⭐ PERFECT!" if entry.get('perfect', False) else ""
        
        col1, col2, col3, col4, col5 = st.columns([0.5, 2, 1.5, 1.5, 1.5])
        
        with col1:
            st.write(medal)
        with col2:
            st.write(f"**Score: {entry['score']} pts**")
        with col3:
            st.write(f"🎯 {entry['difficulty'].upper()}")
        with col4:
            st.write(f"⏱️ {entry['time']}s | 🔹 {entry['guesses']}")
        with col5:
            st.write(perfect_badge)

# ============ GAME FUNCTIONS ============
def reset_game():
    """Reset game to initial state"""
    st.session_state.game_state = 'menu'
    st.session_state.guesses = []
    st.session_state.score = 0
    st.session_state.start_time = None
    st.session_state.elapsed_time = 0
    st.session_state.combo = 0
    st.session_state.perfect_game = False

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
    st.session_state.combo = 0
    st.session_state.perfect_game = True
    
    import time
    st.session_state.start_time = time.time()
    
    # Play start sound
    if st.session_state.sound_enabled:
        try:
            sound = generate_click_sound()
            st.audio(audio_to_html(sound, autoplay=True), format='audio/wav')
        except:
            pass

def check_guess(guess):
    """Check the player's guess"""
    try:
        guess_num = int(guess)
        
        # Validate range
        max_range = 50 if st.session_state.difficulty == 'easy' else \
                   100 if st.session_state.difficulty == 'medium' else 500
        
        if guess_num < 1 or guess_num > max_range:
            st.warning(f"❌ Please enter a number between 1 and {max_range}!")
            return False
        
        # Check if already guessed
        if guess_num in st.session_state.guesses:
            st.warning(f"⚠️ You already guessed {guess_num}!")
            return False
        
        st.session_state.guesses.append(guess_num)
        
        # Check if correct
        if guess_num == st.session_state.target_number:
            st.session_state.game_state = 'game_over'
            # Calculate score based on attempts
            attempts_left = st.session_state.max_attempts - len(st.session_state.guesses) + 1
            difficulty_multiplier = {'easy': 1, 'medium': 2, 'hard': 3}
            st.session_state.score = max(0, attempts_left * 100 * difficulty_multiplier[st.session_state.difficulty])
            
            # Bonus for perfect game (no wrong guesses)
            if len(st.session_state.guesses) == 1:
                st.session_state.score += 500
                st.session_state.perfect_game = True
            
            import time
            st.session_state.elapsed_time = int(time.time() - st.session_state.start_time)
            
            # Play success sound
            if st.session_state.sound_enabled:
                try:
                    sound = generate_success_sound()
                    st.audio(audio_to_html(sound, autoplay=True), format='audio/wav')
                except:
                    pass
            
            return True
        
        # Check if out of attempts
        elif len(st.session_state.guesses) >= st.session_state.max_attempts:
            st.session_state.game_state = 'game_over'
            st.session_state.score = 0
            st.session_state.perfect_game = False
            
            import time
            st.session_state.elapsed_time = int(time.time() - st.session_state.start_time)
            
            # Play failure sound
            if st.session_state.sound_enabled:
                try:
                    sound = generate_failure_sound()
                    st.audio(audio_to_html(sound, autoplay=True), format='audio/wav')
                except:
                    pass
            
            return True
        
        else:
            # Wrong guess but game continues
            st.session_state.combo += 1
            if st.session_state.sound_enabled:
                try:
                    sound = generate_failure_sound()
                    st.audio(audio_to_html(sound, autoplay=True), format='audio/wav')
                except:
                    pass
            
            return False
    
    except ValueError:
        st.warning("❌ Please enter a valid number!")
        return False

def get_difficulty_emoji(difficulty):
    """Get emoji based on difficulty"""
    emojis = {
        'easy': '🟢',
        'medium': '🟡',
        'hard': '🔴'
    }
    return emojis.get(difficulty, '⚪')

def create_progress_bar(current, total):
    """Create a visual progress bar"""
    percentage = (current / total) * 100
    return f"""
    <div class="progress-bar">
        <div class="progress-fill" style="width: {percentage}%"></div>
    </div>
    <p style="text-align: center; font-weight: bold; color: white;">
        {current} / {total} Attempts Used
    </p>
    """

# ============ MAIN UI ============
st.markdown('<h1 class="main-title">🎮 Number Guessing Game</h1>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("---")
    
    # Sound toggle
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("### 🔊 Sound Effects")
    with col2:
        st.session_state.sound_enabled = st.toggle("ON", value=st.session_state.sound_enabled)
    
    st.markdown("---")
    st.write("### 📊 Game Statistics")
    
    leaderboard = load_leaderboard()
    if leaderboard:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Games", len(leaderboard))
        with col2:
            perfect_games = sum(1 for entry in leaderboard if entry.get('perfect', False))
            st.metric("Perfect 🌟", perfect_games)
        
        st.metric("Top Score", f"{leaderboard[0]['score']} pts")
        st.metric("Best Time", f"{min(entry['time'] for entry in leaderboard)}s")
    else:
        st.info("No games played yet!")
    
    st.markdown("---")
    st.write("### 📖 How to Play:")
    with st.expander("Click to expand", expanded=False):
        st.info("""
        🎯 **Your Goal:**
        Guess the computer's secret number!
        
        🎮 **Gameplay:**
        1. Select difficulty level
        2. Computer picks a random number
        3. Guess the number in limited attempts
        4. Get hints: ⬆️ too low, ⬇️ too high
        
        ⭐ **Win Conditions:**
        - Guess correctly before attempts run out
        - Win more points for fewer guesses!
        - Get a PERFECT game (1st guess) for 500 bonus points!
        """)
    
    st.markdown("---")
    st.write("### 🎯 Scoring System:")
    with st.expander("Click to expand", expanded=False):
        st.write("""
        **Multipliers:**
        - 🟢 Easy: 1x
        - 🟡 Medium: 2x
        - 🔴 Hard: 3x
        
        **Formula:**
        Base = (Attempts Left × 100) × Difficulty
        
        **Bonuses:**
        - ⭐ Perfect Game (1st guess): +500 pts
        """)

# ============ MENU SCREEN ============
if st.session_state.game_state == 'menu':
    st.write("---")
    st.write("### 🎮 Select Your Challenge:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🟢 EASY\n(1-50)\n15 Attempts", use_container_width=True, key="easy_btn", help="Perfect for beginners!"):
            start_game('easy')
            st.rerun()
    
    with col2:
        if st.button("🟡 MEDIUM\n(1-100)\n10 Attempts", use_container_width=True, key="medium_btn", help="Balanced difficulty!"):
            start_game('medium')
            st.rerun()
    
    with col3:
        if st.button("🔴 HARD\n(1-500)\n8 Attempts", use_container_width=True, key="hard_btn", help="For the brave!"):
            start_game('hard')
            st.rerun()
    
    st.write("---")
    
    # Fun facts/tips section
    st.markdown("""
    <div class="game-card">
        <h3>💡 Pro Tips</h3>
        <p>💭 Think strategically - each guess gives you valuable information!</p>
        <p>🎯 Try to narrow down the range with each guess</p>
        <p>⚡ Speed matters - complete faster for potential bonus points</p>
        <p>⭐ Guess right on the first try for a PERFECT game!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Leaderboard section
    st.write("---")
    st.write("### 🏆 TOP PLAYERS")
    display_leaderboard()

# ============ PLAYING SCREEN ============
elif st.session_state.game_state == 'playing':
    import time
    
    # Sidebar with game info
    with st.sidebar:
        st.write("### 📊 Game Info")
        st.markdown(f'<div class="score-board">🎯 Difficulty: {get_difficulty_emoji(st.session_state.difficulty)} {st.session_state.difficulty.upper()}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="score-board">❤️ Attempts Left: {st.session_state.max_attempts - len(st.session_state.guesses)}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="score-board">📍 Guesses Made: {len(st.session_state.guesses)}</div>', unsafe_allow_html=True)
        
        # Timer
        elapsed = int(time.time() - st.session_state.start_time)
        st.markdown(f'<div class="score-board">⏱️ Time: {elapsed}s</div>', unsafe_allow_html=True)
        
        # Progress bar
        if st.session_state.guesses:
            st.markdown(create_progress_bar(len(st.session_state.guesses), st.session_state.max_attempts), unsafe_allow_html=True)
            st.write("---")
            st.write("**📝 Your Guesses:**")
            guesses_str = ", ".join(f"🔹{g}" for g in st.session_state.guesses)
            st.write(guesses_str)
    
    # Main game area
    max_range = 50 if st.session_state.difficulty == 'easy' else \
               100 if st.session_state.difficulty == 'medium' else 500
    
    st.markdown(f"""
    <div class="game-card">
        <h2>🎯 Guess the Number!</h2>
        <h3>{1} to {max_range}</h3>
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
        if st.button("🎯 GUESS!", use_container_width=True, key="guess_btn"):
            result = check_guess(guess_input)
            st.rerun()
    
    # Show feedback on previous guesses
    if st.session_state.guesses:
        st.write("---")
        st.write("### 💡 Latest Feedback:")
        last_guess = st.session_state.guesses[-1]
        
        if last_guess < st.session_state.target_number:
            st.markdown(
                f'<div class="feedback-good">📈 {last_guess} is too LOW!</div>',
                unsafe_allow_html=True
            )
        elif last_guess > st.session_state.target_number:
            st.markdown(
                f'<div class="feedback-bad">📉 {last_guess} is too HIGH!</div>',
                unsafe_allow_html=True
            )
    
    # Fun encouragement messages
    attempts_left = st.session_state.max_attempts - len(st.session_state.guesses)
    
    if attempts_left == 1:
        st.warning("⚠️ Last attempt! Go for it! 🚀")
    elif attempts_left == 2:
        st.info("💪 Getting close! Stay focused!")
    elif len(st.session_state.guesses) >= st.session_state.max_attempts // 2:
        st.info("🔥 Halfway there! You got this!")

# ============ GAME OVER SCREEN ============
elif st.session_state.game_state == 'game_over':
    if st.session_state.guesses and st.session_state.guesses[-1] == st.session_state.target_number:
        # WIN STATE
        st.markdown(
            f'<div class="win-message">🎉 YOU WON! 🎉</div>',
            unsafe_allow_html=True
        )
        st.balloons()
        
        # Celebrate emoji rain
        emojis = ['🎉', '⭐', '🎯', '🏆', '✨', '🌟']
        for _ in range(5):
            st.write(" ".join([f"<span class='emoji-rain'>{random.choice(emojis)}</span>" for _ in range(8)]), unsafe_allow_html=True)
        
        st.write("---")
        
        # Stats display
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f'<div class="stat-card"><h3>🎯</h3><h4>{st.session_state.target_number}</h4><p>Target</p></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="stat-card"><h3>📍</h3><h4>{len(st.session_state.guesses)}</h4><p>Guesses</p></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="stat-card"><h3>⭐</h3><h4>{st.session_state.score}</h4><p>Points</p></div>', unsafe_allow_html=True)
        with col4:
            st.markdown(f'<div class="stat-card"><h3>⏱️</h3><h4>{st.session_state.elapsed_time}s</h4><p>Time</p></div>', unsafe_allow_html=True)
        
        st.write("---")
        
        # Perfect game badge
        if st.session_state.perfect_game and len(st.session_state.guesses) == 1:
            st.markdown(
                '<div class="combo-counter">⭐ PERFECT GAME! 500 BONUS POINTS! ⭐</div>',
                unsafe_allow_html=True
            )
        
        st.write("**📝 Your guess sequence:**")
        cols = st.columns(min(len(st.session_state.guesses), 5))
        for i, guess in enumerate(st.session_state.guesses):
            with cols[i % 5]:
                st.markdown(f'<div class="stat-card"><h3>🔹</h3><h2>{guess}</h2></div>', unsafe_allow_html=True)
        
        st.write("---")
        
        # Save score
        add_score(
            st.session_state.score,
            st.session_state.difficulty,
            st.session_state.elapsed_time,
            len(st.session_state.guesses),
            st.session_state.perfect_game and len(st.session_state.guesses) == 1
        )
        
        st.success(f"✅ Score saved to leaderboard!")
    
    else:
        # LOSE STATE
        st.markdown(
            f'<div class="lose-message">😢 GAME OVER 😢</div>',
            unsafe_allow_html=True
        )
        
        st.write("---")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f'<div class="stat-card"><h3>🎯</h3><h4>{st.session_state.target_number}</h4><p>Answer</p></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="stat-card"><h3>📍</h3><h4>{len(st.session_state.guesses)}</h4><p>Guesses</p></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="stat-card"><h3>⭐</h3><h4>0</h4><p>Points</p></div>', unsafe_allow_html=True)
        with col4:
            st.markdown(f'<div class="stat-card"><h3>⏱️</h3><h4>{st.session_state.elapsed_time}s</h4><p>Time</p></div>', unsafe_allow_html=True)
        
        st.write("---")
        st.write("**📝 Your guesses were:**")
        st.write(", ".join(map(str, st.session_state.guesses)))
        
        # Encouragement message
        st.info("💪 Don't worry! Try again with a different strategy. You'll get it next time!")
    
    st.write("---")
    st.write("### 🎮 What's Next?")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Play Again", use_container_width=True, key="play_again", help="Play the same difficulty"):
            reset_game()
            st.rerun()
    
    with col2:
        if st.button("🆙 Change Difficulty", use_container_width=True, key="change_difficulty", help="Go back to menu"):
            reset_game()
            st.session_state.game_state = 'menu'
            st.rerun()
    
    with col3:
        if st.button("🏆 View Leaderboard", use_container_width=True, key="view_leaderboard", help="See all top scores"):
            reset_game()
            st.session_state.game_state = 'menu'
            st.rerun()
