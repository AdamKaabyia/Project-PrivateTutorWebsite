from server_requests import *
import streamlit as st
from update_meeting import handle_meeting_actions
from datetime import datetime


def student_view():
    """Student Dashboard."""
    logger.info("Loading Student Dashboard.")
    st.subheader("Student Dashboard")
    options = ["My Profile", "Available Teachers", "Edit Profile", "My Meetings"]

    choice = st.sidebar.radio("Menu", options)

    if choice == "Available Teachers":
        st.subheader("🧑‍🏫 Available Teachers")

        try:
            teachers = fetch_data("/teachers/")
            if teachers:
                for teacher in teachers:
                    if teacher.get("id") == st.session_state.get("user_id"):
                        continue

                    name = teacher.get("name", "N/A")
                    email = teacher.get("email", "N/A")
                    phone = teacher.get("phone", "N/A")
                    rate = teacher.get("hourly_rate", "N/A")
                    rating = teacher.get("rating", "N/A")
                    subjects = ", ".join(teacher.get("subjects_to_teach", []))
                    availability = teacher.get("available", [])

                    availability_str = ""
                    for interval in availability:
                        try:
                            start = datetime.fromisoformat(interval["start"]).strftime("%A, %B %d, %Y at %I:%M %p")
                            end = datetime.fromisoformat(interval["end"]).strftime("%I:%M %p")
                            availability_str += f"📅 {start} → {end}<br>"
                        except:
                            availability_str += f"{interval.get('start', '')} → {interval.get('end', '')}<br>"

                    st.markdown(f"""
                        <div style='background-color:#2c2f33; padding:15px; border-radius:10px; margin-bottom:20px; color:#f0f0f0'>
                            <h4>👤 <strong>{name}</strong></h4>
                            <p>📧 <strong>Email:</strong> {email}<br>
                               📞 <strong>Phone:</strong> {phone}<br>
                               💰 <strong>Hourly Rate:</strong> ${rate}<br>
                               ⭐ <strong>Rating:</strong> {rating}/5<br>
                               📘 <strong>Subjects:</strong> {subjects}<br>
                               ⏱️ <strong>Availability:</strong><br>{availability_str}</p>
                            <form action='#'>
                                <button style='background-color:#4CAF50; color:white; border:none; padding:10px 15px; border-radius:5px; cursor:pointer'
                                        onclick="document.getElementById('{teacher.get("id")}').click(); return false;">
                                    Request Meeting with {name}
                                </button>
                            </form>
                        </div>
                    """, unsafe_allow_html=True)

                    st.button(f"", key=teacher.get("id"), on_click=request_meeting_with_teacher, args=(teacher,))
            else:
                st.info("No teachers found.")
        except Exception as e:
            logger.exception("Error fetching teachers.")
            st.error("Failed to load teacher data. Please try again later.")

    elif choice == "My Meetings":
        st.subheader("Your Meetings")
        try:
            student_meetings = get_my_meetings(st.session_state.user_id)
            if student_meetings:
                for meeting in student_meetings:
                    st.write(f"**Subject:** {meeting.get('topic', 'N/A')}")
                    st.write(f"**Teacher:** {meeting.get('teacher_name', 'N/A')}")
                    st.write(f"**Scheduled Time:** {meeting.get('scheduled_time', 'N/A')}")
                    if st.button(f"Cancel Meeting: {meeting.get('topic')}", key=meeting.get('id')):
                        handle_meeting_actions(meeting.get('id'), "Cancel")
                    st.write("---")
            else:
                logger.info("No meetings found for student.")
                st.info("No meetings found.")
        except Exception as e:
            logger.exception("Error fetching meetings for student.")
            st.error("Failed to load meetings. Please try again later.")
    # -------------------------
    # Edit Profile Section
    # -------------------------
    elif choice == "Edit Profile":
        st.subheader("🛠️ Edit Your Profile")
        user_id = st.session_state.get("user_id")
        try:
            existing_data = fetch_data(f"/students/{user_id}")
            if not existing_data:
                st.error("Failed to load your profile.")
            else:
                # --- Pre-fill form fields
                name = st.text_input("Full Name", value=existing_data.get("name", ""))
                about_section = st.text_area("About Me", value=existing_data.get("about_section", ""))
                phone = st.text_input("Phone Number", value=existing_data.get("phone", ""))
                email = st.text_input("Email", value=existing_data.get("email", ""))
                # --- Define your master list of allowed subjects
                all_subjects = [

                    "Math", "Physics", "Chemistry", "Biology",

                    "English", "Computer Science", "History", "Economics"

                ]
                # --- Normalize existing subjects into the same casing
                raw = existing_data.get("subjects_interested_in_learning", [])
                default_subjects = [s.title() for s in raw]  # e.g. "chemistry" → "Chemistry"
                # --- Now the defaults all appear in `all_subjects`
                selected_subjects = st.multiselect("Subjects Interested In", options=all_subjects,
                                                   default=default_subjects)
                if st.button("Update Profile"):
                    updated_data = existing_data.copy()
                    updated_data["name"] = name.strip()
                    updated_data["about_section"] = about_section.strip()
                    updated_data["phone"] = phone.strip()
                    updated_data["email"] = email.strip()
                    # If you want to send them back as lowercase, map `.lower()` here; otherwise leave as-is
                    updated_data["subjects_interested_in_learning"] = [s.lower() for s in selected_subjects]
                    ok1 = send_data(f"/students/{user_id}", updated_data, method="PUT")
                    user_payload = {"email": email.strip()}
                    ok2 = send_data(f"/users/{user_id}", user_payload, method="PUT")
                    if ok1 and ok2:
                        # keep your session in sync
                        st.session_state["user_email"] = email.strip()
                        st.success("Profile (and login email) updated successfully!")
                    else:
                        st.error("Something went wrong updating your profile/email.")
        except Exception:
            logger.exception("Failed to load student profile for editing.")
            st.error("An unexpected error occurred while loading your profile.")

    elif choice == "My Profile":
        st.subheader("📋 My Profile")

        try:
            user_id = st.session_state.get("user_id")
            student_data = fetch_data(f"/students/{user_id}")

            if student_data:
                st.markdown("### 👤 Personal Information")
                st.write(f"**Name:** {student_data.get('name', 'N/A')}")
                st.write(f"**Email:** {student_data.get('email', 'N/A')}")
                st.write(f"**Phone:** {student_data.get('phone', 'N/A')}")

                st.markdown("### 🧾 About Me")
                st.write(student_data.get("about_section", "_No info provided._"))

                st.markdown("### 📚 Subjects Interested In")
                subjects = student_data.get("subjects_interested_in_learning", [])
                st.write(", ".join(subjects) if subjects else "_None listed._")

                st.markdown("### 🕒 Availability")
                availability = student_data.get("available", [])
                if availability:
                    for i, interval in enumerate(availability):
                        try:
                            start_dt = datetime.fromisoformat(interval.get("start", ""))
                            end_dt = datetime.fromisoformat(interval.get("end", ""))
                            start_str = start_dt.strftime("%A, %B %d, %Y at %I:%M %p")
                            end_str = end_dt.strftime("%A, %B %d, %Y at %I:%M %p")

                            html = (
                                f"<span style='color:gold'><strong>From:</strong></span> {start_str} → "
                                f"<span style='color:gold'><strong>To:</strong></span> {end_str}"
                            )
                            st.markdown(f"{i + 1}. {html}", unsafe_allow_html=True)
                        except Exception as e:
                            st.write(
                                f"{i + 1}. **From:** {interval.get('start', 'N/A')} → **To:** {interval.get('end', 'N/A')}")
                else:
                    st.write("_No availability set._")

            else:
                st.warning("Unable to fetch profile data. Please try again later.")
        except Exception as e:
            logger.exception("Failed to load student profile.")
            st.error("An unexpected error occurred while loading your profile.")
