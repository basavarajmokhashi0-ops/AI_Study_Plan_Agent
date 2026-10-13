from database import (
    save_study_plan,
    get_saved_plans,
    load_study_plan,
    update_study_plan
)
import streamlit as st
import pandas as pd
from datetime import date, timedelta

from database import (
    save_study_plan,
    get_saved_plans,
    load_study_plan,
    update_study_plan
)

# ---------------- PAGE CONFIGURATION ----------------

st.set_page_config(
    page_title="AI Study Plan Agent",
    page_icon="📚",
    layout="wide"
)

# ---------------- APPLICATION TITLE ----------------

st.title("📚 AI Study Plan Agent")
st.write(
    "Create a personalized study plan based on your subjects, "
    "difficulty levels, and priorities."
)

st.divider()

# ---------------- STUDENT DETAILS ----------------

st.sidebar.header("Student Details")

student_name = st.sidebar.text_input(
    "Enter your name",
    placeholder="Your name"
)

exam_date = st.sidebar.date_input(
    "Exam date",
    value=date.today() + timedelta(days=7),
    min_value=date.today()
)

study_hours = st.sidebar.slider(
    "Available study hours per day",
    min_value=1,
    max_value=12,
    value=4
)

learning_level = st.sidebar.selectbox(
    "Your learning level",
    ["Beginner", "Intermediate", "Advanced"]
)

# ---------------- LOAD SAVED PLANS ----------------

st.sidebar.divider()
st.sidebar.header("💾 Saved Study Plans")

try:
    saved_plans = get_saved_plans()
except Exception as error:
    st.sidebar.error(f"Could not retrieve saved plans: {error}")
    saved_plans = pd.DataFrame()

if not saved_plans.empty:
    saved_plan_ids = saved_plans["id"].astype(int).tolist()

    def format_saved_plan(plan_id):
        matching = saved_plans[
            saved_plans["id"].astype(int) == int(plan_id)
        ]

        if matching.empty:
            return f"Plan #{plan_id}"

        row = matching.iloc[0]
        return (
            f"#{int(row['id'])} - {row['student_name']} "
            f"({row['created_at']})"
        )

    selected_plan_id = st.sidebar.selectbox(
        "Choose a saved plan",
        options=saved_plan_ids,
        format_func=format_saved_plan,
        key="selected_saved_plan_id"
    )

    if st.sidebar.button("📂 Load Selected Plan"):
        try:
            selected_row = saved_plans[
                saved_plans["id"].astype(int)
                == int(selected_plan_id)
            ].iloc[0]

            loaded_schedule = load_study_plan(
                int(selected_plan_id)
            )

            if loaded_schedule is None:
                st.sidebar.error("The selected plan could not be loaded.")
            else:
                st.session_state["study_plan"] = loaded_schedule
                st.session_state["student_name"] = (
                    selected_row["student_name"]
                )
                st.session_state["current_plan_id"] = int(
                    selected_plan_id
                )

                st.session_state["plan_settings"] = {
                    "exam_date": date.fromisoformat(
                        str(selected_row["exam_date"])[:10]
                    ),
                    "study_hours": int(selected_row["study_hours"]),
                    "learning_level": selected_row["learning_level"]
                }

                # Clear the editor's previous data
                st.session_state.pop("study_plan_editor", None)

                st.rerun()

        except Exception as error:
            st.sidebar.error(f"Error loading plan: {error}")

else:
    st.sidebar.info("No saved study plans yet.")

# ---------------- SUBJECT INPUT ----------------

st.subheader("📖 Enter Your Subjects")

subjects_text = st.text_area(
    "Enter one subject per line",
    placeholder=(
        "Database Management Systems\n"
        "Python Programming\n"
        "Computer Networks\n"
        "Operating Systems"
    ),
    height=130
)

# Remove empty lines and duplicate subjects
subjects = list(dict.fromkeys(
    subject.strip()
    for subject in subjects_text.splitlines()
    if subject.strip()
))

# ---------------- SUBJECT DIFFICULTY AND PRIORITY ----------------

st.subheader("🎯 Subject Difficulty and Priority")

subject_details = {}

if subjects:
    for subject in subjects:
        with st.expander(
            f"Settings for {subject}",
            expanded=True
        ):
            col1, col2 = st.columns(2)

            with col1:
                difficulty_level = st.selectbox(
                    f"Difficulty: {subject}",
                    ["Easy", "Medium", "Hard"],
                    index=1,
                    key=f"difficulty_{subject}"
                )

            with col2:
                priority = st.selectbox(
                    f"Priority: {subject}",
                    ["Low", "Medium", "High"],
                    index=1,
                    key=f"priority_{subject}"
                )

            subject_details[subject] = {
                "difficulty": difficulty_level,
                "priority": priority
            }
else:
    st.info(
        "Enter your subjects above to configure their "
        "difficulty and priority."
    )

# ---------------- GENERATE STUDY PLAN ----------------

if st.button("🚀 Generate Study Plan", type="primary"):

    if not subjects:
        st.warning("Please enter at least one subject.")

    else:
        today = date.today()
        total_days = (exam_date - today).days + 1

        schedule = []

        # Assign greater weights to harder and higher-priority subjects
        difficulty_weights = {
            "Easy": 1,
            "Medium": 2,
            "Hard": 3
        }

        priority_weights = {
            "Low": 1,
            "Medium": 2,
            "High": 3
        }

        subject_weights = {}

        for subject in subjects:
            details = subject_details[subject]

            weight = (
                difficulty_weights[details["difficulty"]]
                * priority_weights[details["priority"]]
            )

            subject_weights[subject] = weight

        # Create a weighted subject rotation
        weighted_subjects = []

        for subject in subjects:
            weighted_subjects.extend(
                [subject] * subject_weights[subject]
            )

        # Generate the daily schedule
        for day_number in range(total_days):
            study_date = today + timedelta(days=day_number)

            for session_number in range(study_hours):
                subject_index = (
                    day_number * study_hours + session_number
                ) % len(weighted_subjects)

                subject = weighted_subjects[subject_index]
                details = subject_details[subject]

                schedule.append({
                    "Date": study_date.strftime("%d-%m-%Y"),
                    "Day": study_date.strftime("%A"),
                    "Session": f"Session {session_number + 1}",
                    "Subject": subject,
                    "Duration": "1 hour",
                    "Difficulty": details["difficulty"],
                    "Priority": details["priority"],
                    "Learning Level": learning_level,
                    "Status": "Pending"
                })

        # Store the generated schedule in session state
        study_plan = pd.DataFrame(schedule)
        saved_student_name = student_name.strip() or "Student"

        st.session_state["study_plan"] = study_plan
        st.session_state["student_name"] = saved_student_name

        st.session_state["plan_settings"] = {
            "exam_date": exam_date,
            "study_hours": study_hours,
            "learning_level": learning_level
        }

        # Clear the editor state when generating a new plan
        st.session_state.pop("study_plan_editor", None)

        try:
            # Save the new plan to SQLite
            plan_id = save_study_plan(
                student_name=saved_student_name,
                exam_date=exam_date,
                study_hours=study_hours,
                learning_level=learning_level,
                schedule=study_plan
            )

            st.session_state["current_plan_id"] = plan_id

            st.success(
                f"Study plan generated and saved successfully! "
                f"Plan ID: {plan_id}"
            )

        except Exception as error:
            st.error(
                f"The study plan was generated, but saving failed: {error}"
            )

# ---------------- DISPLAY STUDY PLAN ----------------

if "study_plan" in st.session_state:

    st.divider()

    st.success(
        f"Study plan for {st.session_state['student_name']}!"
    )

    settings = st.session_state["plan_settings"]

    st.write(f"**Exam date:** {settings['exam_date']}")
    st.write(
        f"**Daily study sessions:** {settings['study_hours']}"
    )
    st.write(
        f"**Learning level:** {settings['learning_level']}"
    )

    current_plan_id = st.session_state.get("current_plan_id")

    if current_plan_id is not None:
        st.caption(f"Saved database plan ID: {current_plan_id}")

    st.subheader("📅 Your Study Schedule")

    edited_df = st.data_editor(
        st.session_state["study_plan"],
        use_container_width=True,
        hide_index=True,
        key="study_plan_editor",
        column_config={
            "Status": st.column_config.SelectboxColumn(
                "Study Status",
                options=["Pending", "Completed"],
                required=True
            )
        },
        disabled=[
            "Date",
            "Day",
            "Session",
            "Subject",
            "Duration",
            "Difficulty",
            "Priority",
            "Learning Level"
        ]
    )

    # Preserve changes to session statuses
    st.session_state["study_plan"] = edited_df

    # Automatically update the saved plan in SQLite
    if current_plan_id is not None:
        try:
            update_study_plan(
                int(current_plan_id),
                edited_df
            )
            st.caption("Progress is saved automatically.")
        except Exception as error:
            st.error(f"Could not save progress: {error}")

    # ---------------- PROGRESS TRACKING ----------------

    st.subheader("📊 Study Progress")

    total_sessions = len(edited_df)

    completed_sessions = int(
        (edited_df["Status"] == "Completed").sum()
    )

    pending_sessions = total_sessions - completed_sessions

    progress = (
        completed_sessions / total_sessions
        if total_sessions > 0
        else 0
    )

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Sessions", total_sessions)
    col2.metric("Completed Sessions", completed_sessions)
    col3.metric("Pending Sessions", pending_sessions)

    st.progress(
        float(progress),
        text=f"Overall completion: {progress:.0%}"
    )

    # ---------------- STUDY RECOMMENDATIONS ----------------

    st.subheader("💡 Study Recommendations")

    # Derive recommendations from the displayed plan,
    # including when an older plan has been loaded.
    high_priority_subjects = (
        edited_df.loc[
            edited_df["Priority"] == "High", "Subject"
        ].drop_duplicates().tolist()
    )

    hard_subjects = (
        edited_df.loc[
            edited_df["Difficulty"] == "Hard", "Subject"
        ].drop_duplicates().tolist()
    )

    if high_priority_subjects:
        st.write(
            "**High-priority subjects:** "
            + ", ".join(high_priority_subjects)
        )

    if hard_subjects:
        st.write(
            "**Subjects needing extra practice:** "
            + ", ".join(hard_subjects)
        )

    if progress == 1:
        st.success(
            "Excellent! You have completed every study session."
        )
    elif progress >= 0.5:
        st.info(
            "Good progress! Continue studying and revise "
            "completed topics."
        )
    else:
        st.info(
            "Start with your scheduled sessions and focus on "
            "difficult and high-priority subjects."
        )

    # ---------------- CSV DOWNLOAD ----------------

    st.subheader("⬇️ Download Your Study Plan")

    csv_data = edited_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download Study Plan as CSV",
        data=csv_data,
        file_name="study_plan.csv",
        mime="text/csv"
    )

# ---------------- FOOTER ----------------

st.divider()

st.caption(
    "AI Study Plan Agent | Built with Python, Pandas, "
    "Streamlit, and SQLite"
)
