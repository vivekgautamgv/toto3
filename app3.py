import streamlit as st
import json
import os
from datetime import datetime, timedelta

DATA_FILE = "goals_data.json"

# ---------------- Helper Functions ----------------
def load_data():
    if not os.path.exists(DATA_FILE) or os.stat(DATA_FILE).st_size == 0:
        with open(DATA_FILE, "w") as f:
            json.dump({}, f)
    with open(DATA_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def is_active(timestamp_str):
    goal_time = datetime.fromisoformat(timestamp_str)
    return datetime.now() - goal_time < timedelta(hours=24)

# ---------------- Load & Setup ----------------
st.set_page_config(page_title="Goals Tracker", layout="centered")
st.title("📋 Daily ToDo & Goals Tracker (24h)")

data = load_data()
now = datetime.now()

# ---------------- User Login ----------------
username = st.text_input("Enter your name").strip()

if username:
    # Create new user or reset timestamp if expired
    if username not in data or not is_active(data[username]["timestamp"]):
        if st.button("🔁 Start New Day / Reset All"):
            data[username] = {
                "timestamp": now.isoformat(),
                "goals": [],
                "remarks": {}
            }
            save_data(data)
            st.success("New goal session started!")

    # Load user’s current data
    user_data = data.get(username, {"goals": [], "timestamp": now.isoformat(), "remarks": {}})
    user_goals = user_data.get("goals", [])

    # ---------------- Add Goals ----------------
    st.subheader("Your Daily Goals")
    if "new_goals" not in st.session_state:
        st.session_state.new_goals = []

    for i, goal in enumerate(st.session_state.new_goals):
        st.session_state.new_goals[i] = st.text_input(f"Goal {i+1}", value=goal, key=f"goal_input_{i}")

    if st.button("➕ Add Goal"):
        st.session_state.new_goals.append("")

    if st.session_state.new_goals and st.button("💾 Save Goals"):
        new_goals = [{"task": task, "done": False, "completed_at": None} for task in st.session_state.new_goals if task.strip()]
    
    # Ensure user exists before updating
        if username not in data:
            data[username] = {
                "timestamp": now.isoformat(),
                "goals": [],
                "remarks": {}
            }
    
        data[username]["timestamp"] = now.isoformat()
        data[username]["goals"].extend(new_goals)
        save_data(data)
        st.session_state.new_goals = []
        st.success("Goals saved!")


    # ---------------- Checklist & Reset Individual Goals ----------------
    if user_goals and is_active(user_data["timestamp"]):
        st.markdown("### ✅ Your Checklist")
        updated_goals = []
        for i, goal in enumerate(user_goals):
            cols = st.columns([0.7, 0.2, 0.1])
            with cols[0]:
                checked = cols[0].checkbox(goal["task"], value=goal["done"], key=f"{username}_chk_{i}")
            with cols[1]:
                if checked and not goal["done"]:
                    goal["completed_at"] = now.isoformat()
                elif not checked:
                    goal["completed_at"] = None
                goal["done"] = checked
            with cols[2]:
                if st.button("❌", key=f"del_{i}"):
                    continue  # Skip adding this goal
            updated_goals.append(goal)

        data[username]["goals"] = updated_goals
        save_data(data)

        # Show time of completion
        for goal in updated_goals:
            if goal["done"] and goal["completed_at"]:
                ts = datetime.fromisoformat(goal["completed_at"]).strftime("%I:%M %p")
                st.caption(f"🕒 Completed at {ts}")

        # Reset All Button
        if st.button("🔁 Reset All Goals (Manual)"):
            data[username]["goals"] = []
            data[username]["timestamp"] = now.isoformat()
            save_data(data)
            st.success("All goals have been reset manually.")

# ---------------- View Others ----------------
st.divider()
st.subheader("👥 View Another User's Activity")

active_users = [u for u in data if u != username and is_active(data[u]["timestamp"])]

if active_users:
    selected_user = st.selectbox("Select user:", active_users)
    if selected_user:
        st.write(f"### 📌 Goals of {selected_user}")
        for goal in data[selected_user]["goals"]:
            msg = f"✅ {goal['task']}" if goal["done"] else f"🔲 {goal['task']}"
            st.write(msg)
            if goal["done"] and goal["completed_at"]:
                ts = datetime.fromisoformat(goal["completed_at"]).strftime("%I:%M %p")
                st.caption(f"🕒 Completed at {ts}")

        # Add remark & rating
        st.markdown("### 💬 Leave a Remark & Rating")
        remark_text = st.text_area("Remark", key="remark_box")
        rating = st.slider("Rate their effort (0-10)", 0, 10, 5, key="rating_slider")
        if st.button("✍️ Submit Remark"):
            data[selected_user]["remarks"][f"from_{username}"] = {
                "text": remark_text,
                "rating": rating
            }
            save_data(data)
            st.success(f"Remark submitted to {selected_user}!")

        # Show received remarks
        if "remarks" in data[selected_user]:
            st.markdown("### 🗨️ Feedback from others:")
            for from_user, val in data[selected_user]["remarks"].items():
                st.write(f"**{from_user}** rated: 🌟 {val['rating']}/10")
                st.write(f"📝 {val['text']}")

else:
    st.info("No other active users yet.")

# ---------------- Admin: Delete All Users ----------------
st.divider()
st.subheader("⚠️ Admin Actions (Danger Zone)")

with st.expander("🗑️ Delete All Users & Reset App"):
    st.warning("This will permanently delete ALL users, goals, remarks, and activity data.")
    
    confirm = st.checkbox("✅ Yes, delete EVERYTHING (no undo)")
    
    if st.button("🔥 DELETE EVERYTHING"):
        if confirm:
            try:
                # Step 1: Clear JSON
                with open(DATA_FILE, "w") as f:
                    json.dump({}, f)
                    f.flush()
                    os.fsync(f.fileno())  # Ensure it's flushed to disk
                
                # Step 2: Clear session state variables
                for key in list(st.session_state.keys()):
                    del st.session_state[key]

                st.success("✅ All users, goals, and feedback deleted.")
                st.rerun()  # Reload app with clean state

            except Exception as e:
                st.error(f"Error deleting data: {e}")
        else:
            st.warning("Please confirm the deletion by checking the box.")

