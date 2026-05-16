# game.py
import streamlit as st
import random
from datetime import datetime

# Initialize session state
if 'game_state' not in st.session_state:
    st.session_state.game_state = 'menu'  # menu, playing, game_over
    st.session_state.target_number = 0
    st.session_state.guesses = []
    st.session_state.difficulty = 'medium'
    st.session_state.max_attempts = 10
    st.session_state.score = 0

st.set_page_config(page_title="🎮 Number Guess Game", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for better styling
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
    }
    .game-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 10px 0;
    }
    .score-board {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 15px;
        border-radius: 10px;
        color: white;
        text-align: center;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def reset_game():
    """Reset game to initial state"""
    st.session_state.game_state = 'menu'
    st.session_state.guesses = []
    st.session_state.score = 0

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

def check_guess(guess):
    """Check the player's guess"""
    try:
        guess_num = int(guess)
        
        if guess_num < 1 or (st.session_state.difficulty == 'easy' and guess_num > 50) or \
           (st.session_state.difficulty == 'medium' and guess_num > 100) or \
           (st.session_state.difficulty == 'hard' and guess_num > 500):
            st.warning(f"Please enter a valid number!")
            return
        
        st.session_state.guesses.append(guess_num)
        
        if guess_num == st.session_state.target_number:
            st.session_state.game_state = 'game_over'
            st.session_state.score = max(0, (st.session_state.max_attempts - len(st.session_state.guesses) + 1) * 10)
        elif len(st.session_state.guesses) >= st.session_state.max_attempts:
            st.session_state.game_state = 'game_over'
            st.session_state.score = 0
    except ValueError:
        st.warning("Please enter a valid number!")

# Main UI
st.markdown('<h1 class="main-title">🎮 Number Guessing Game</h1>', unsafe_allow_html=True)

# Menu Screen
if st.session_state.game_state == 'menu':
    col1, col2, col3 = st.columns(3)
    
    st.write("---")
    st.write("### Select Difficulty Level:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🟢 Easy (1-50)", use_container_width=True, key="easy_btn"):
            start_game('easy')
            st.rerun()
    
    with col2:
        if st.button("🟡 Medium (1-100)", use_container_width=True, key="medium_btn"):
            start_game('medium')
            st.rerun()
    
    with col3:
        if st.button("🔴 Hard (1-500)", use_container_width=True, key="hard_btn"):
            start_game('hard')
            st.rerun()
    
    # Instructions
    st.write("---")
    st.write("### 📖 How to Play:")
    st.info("""
    1. Select your difficulty level
    2. The computer picks a random number
    3. You have a limited number of attempts to guess it
    4. After each guess, you'll get hints: ⬆️ (too low) or ⬇️ (too high)
    5. Guess correctly to win and earn points!
    """)

# Playing Screen
elif st.session_state.game_state == 'playing':
    # Sidebar with game info
    with st.sidebar:
        st.write("### 📊 Game Info")
        st.markdown(f'<div class="score-board">Difficulty: {st.session_state.difficulty.upper()}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="score-board">Attempts Left: {st.session_state.max_attempts - len(st.session_state.guesses)}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="score-board">Guesses Made: {len(st.session_state.guesses)}</div>', unsafe_allow_html=True)
        
        if st.session_state.guesses:
            st.write("**Previous Guesses:**")
            st.write(", ".join(map(str, st.session_state.guesses)))
    
    # Main game area
    st.write(f"### Guess the number! ({1 if st.session_state.difficulty == 'easy' else (1 if st.session_state.difficulty == 'medium' else 1)}-{50 if st.session_state.difficulty == 'easy' else (100 if st.session_state.difficulty == 'medium' else 500)})")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        guess_input = st.number_input("Enter your guess:", min_value=1, value=50, step=1, label_visibility="collapsed")
    
    with col2:
        if st.button("🎯 Guess", use_container_width=True):
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

# Game Over Screen
elif st.session_state.game_state == 'game_over':
    if st.session_state.guesses[-1] == st.session_state.target_number:
        st.success("🎉 CONGRATULATIONS! You won!")
        st.balloons()
        
        st.write("---")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Target Number", st.session_state.target_number)
        with col2:
            st.metric("Your Guesses", len(st.session_state.guesses))
        with col3:
            st.metric("Points Earned", st.session_state.score)
        with col4:
            st.metric("Difficulty", st.session_state.difficulty.upper())
        
        st.write("---")
        st.write("**Your guesses were:**")
        st.write(", ".join(map(str, st.session_state.guesses)))
    
    else:
        st.error("😢 Game Over! You didn't guess the number in time.")
        st.write(f"The number was: **{st.session_state.target_number}**")
        st.write(f"You made {len(st.session_state.guesses)} guesses")
        st.write("**Your guesses were:**")
        st.write(", ".join(map(str, st.session_state.guesses)))
    
    st.write("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Play Again", use_container_width=True, key="play_again"):
            reset_game()
            st.rerun()
    
    with col2:
        if st.button("📊 Back to Menu", use_container_width=True, key="menu"):
            reset_game()
            st.rerun()
