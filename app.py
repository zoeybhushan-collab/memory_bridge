import os
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
import streamlit as st
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DB_NAME = "memory_bridge.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            user_name TEXT,
            mood TEXT,
            activity_type TEXT,
            user_input TEXT,
            ai_response TEXT,
            rating INTEGER
        )
    """)

    conn.commit()
    conn.close()


def save_activity(user_name, mood, activity_type, user_input, ai_response, rating):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO activity_log
        (created_at, user_name, mood, activity_type, user_input, ai_response, rating)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        user_name,
        mood,
        activity_type,
        user_input,
        ai_response,
        rating
    ))

    conn.commit()
    conn.close()


def get_ai_response(user_name, mood, user_message):
    system_prompt = """
    You are Memory Bridge AI, a gentle companion for memory engagement.
    You are not a doctor. You do not diagnose or provide medical advice.
    Your role is to provide warm conversation, simple memory prompts,
    emotional support, and safe cognitive engagement.

    Rules:
    1. Never diagnose dementia or cognitive decline.
    2. Never give medical instructions.
    3. If the user mentions urgent medical distress, advise them to contact a caregiver or emergency services.
    4. Keep responses short, warm, and easy to understand.
    5. Ask one simple follow up question.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"User name: {user_name}. Mood: {mood}. Message: {user_message}"
            }
        ],
        temperature=0.6
    )

    return response.choices[0].message.content


def word_recall_game():
    st.subheader("Memory Game: Word Recall")

    words = ["apple", "chair", "river", "music", "garden"]

    st.write("Please look at these words for 10 seconds:")
    st.write(", ".join(words))

    st.write("Now type as many words as you remember.")
    answer = st.text_input("Your answer")

    if st.button("Check Recall"):
        recalled = [w.strip().lower() for w in answer.split(",")]
        score = len(set(words).intersection(set(recalled)))
        st.success(f"You remembered {score} out of {len(words)} words.")
        return f"Recall score: {score}/{len(words)}"

    return ""


def memory_prompt():
    st.subheader("Memory Prompt")

    prompt = st.selectbox(
        "Choose a topic",
        [
            "A favorite childhood food",
            "A favorite song",
            "A family celebration",
            "A place you loved visiting",
            "A teacher or friend you remember"
        ]
    )

    response = st.text_area("Write or say a short memory about this topic")

    return prompt, response


def caregiver_summary():
    st.subheader("Caregiver Summary")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT created_at, user_name, mood, activity_type, rating
        FROM activity_log
        ORDER BY created_at DESC
        LIMIT 10
    """)

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        st.info("No activity recorded yet.")
        return

    for row in rows:
        st.write({
            "time": row[0],
            "user": row[1],
            "mood": row[2],
            "activity": row[3],
            "rating": row[4]
        })


def main():
    init_db()

    st.title("Memory Bridge AI")
    st.write("A safe AI companion for memory engagement and dementia awareness.")

    st.warning(
        "This app is not a medical device. It does not diagnose, treat, or replace doctors or caregivers."
    )

    user_name = st.text_input("First name", value="Friend")

    mood = st.selectbox(
        "How are you feeling today?",
        ["Happy", "Calm", "Tired", "Lonely", "Confused", "Unsure"]
    )

    page = st.sidebar.radio(
        "Choose Activity",
        ["AI Companion Chat", "Memory Prompt", "Word Recall Game", "Caregiver Summary"]
    )

    if page == "AI Companion Chat":
        st.subheader("AI Companion Chat")

        user_message = st.text_area("Say something to Memory Bridge AI")

        if st.button("Send"):
            if user_message.strip():
                ai_response = get_ai_response(user_name, mood, user_message)
                st.write(ai_response)

                rating = st.slider("Was this helpful?", 1, 5, 3)

                save_activity(
                    user_name,
                    mood,
                    "AI Companion Chat",
                    user_message,
                    ai_response,
                    rating
                )

    elif page == "Memory Prompt":
        prompt, response = memory_prompt()

        if st.button("Save Memory Prompt"):
            save_activity(
                user_name,
                mood,
                "Memory Prompt",
                prompt,
                response,
                5
            )
            st.success("Saved.")

    elif page == "Word Recall Game":
        result = word_recall_game()

        if result:
            save_activity(
                user_name,
                mood,
                "Word Recall Game",
                "Word recall activity",
                result,
                5
            )

    elif page == "Caregiver Summary":
        caregiver_summary()


if __name__ == "__main__":
    main()