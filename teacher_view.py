from server_requests import *
import streamlit as st
from datetime import datetime
from update_meeting import handle_meeting_actions


def teacher_view():
    """Teacher Dashboard."""
    logger.info("Loading Teacher Dashboard.")
    st.subheader("Teacher Dashboard")
    options = ["My Profile", "Edit Availability", "Edit Profile", "Manage Meetings"]
    choice = st.sidebar.radio("Menu", options)

    # -------------------------
    # Manage Meetings Section
    # -------------------------
    if choice == "Manage Meetings":
        st.subheader("Your Meetings")
        try:
            teacher_meetings = get_my_meetings(st.session_state.user_id) or []
            if teacher_meetings:
                for meeting in teacher_meetings:
                    st.write(f"**Subject:** {meeting.get('topic', 'N/A')}")
                    st.write(f"**Student:** {meeting.get('student_name', 'N/A')}")
                    st.write(f"**Scheduled Time:** {meeting.get('scheduled_time', 'N/A')}")
                    action = st.radio(
                        f"Actions for {meeting.get('topic', 'Meeting')}",
                        ["Approve", "Cancel"],
                        key=meeting.get('id', '')
                    )
                    if st.button(f"{action} Meeting: {meeting.get('topic', 'N/A')}",
                                 key=f"{action}_{meeting.get('id', '')}"):
                        handle_meeting_actions(meeting.get('id'), action)
                    st.write("---")
            else:
                logger.info("No meetings found for teacher.")
                st.info("No meetings found.")
        except Exception as e:
            logger.exception("Error loading meetings for teacher.")
            st.error("Failed to load meetings. Please try again later.")

    # -------------------------
    # Edit Availability Section
    # -------------------------
    elif choice == "Edit Availability":
        st.subheader("Edit Your Availability")
        st.markdown("Add available time slots below:")

        # --- Date/time inputs
        start_date = st.date_input("Start Date", key="edit_start_date")
        start_time = st.time_input("Start Time", key="edit_start_time")
        end_date = st.date_input("End Date", key="edit_end_date")
        end_time = st.time_input("End Time", key="edit_end_time")

        # Combine into datetime
        start_dt = datetime.combine(start_date, start_time)
        end_dt = datetime.combine(end_date, end_time)

        if "edit_availability" not in st.session_state:
            try:
                teacher_data = fetch_data(f"/teachers/{st.session_state.user_id}")
                if isinstance(teacher_data, dict):
                    saved_avail = teacher_data.get("available", [])
                else:
                    st.warning("Unexpected response format for teacher data.")
                    saved_avail = []
            except Exception as e:
                saved_avail = []
                st.error("Could not load saved availability.")
                logger.exception("Failed to fetch existing availability.")
            else:
                st.session_state.edit_availability = saved_avail

        # Add interval
        if st.button("➕ Add Time Interval"):
            if end_dt <= start_dt:
                st.error("End time must be after start time.")
            else:
                st.session_state.edit_availability.append({
                    "start": start_dt.isoformat(),
                    "end": end_dt.isoformat()
                })
                st.success("Interval added!")

        # --- Display current availability
        st.markdown("### 🕒 Current Availability:")

        for i, interval in enumerate(st.session_state.edit_availability):
            try:
                start = datetime.fromisoformat(interval.get('start'))
                end = datetime.fromisoformat(interval.get('end'))
                formatted = f"📅 {start.strftime('%A, %d %B %Y')}<br>⏰ {start.strftime('%H:%M')} → {end.strftime('%H:%M')}"

                st.markdown(f"""
                <div style='background-color:#2c2f33; padding:10px; border-radius:6px; margin-bottom:10px; color:#f0f0f0'>
                    <strong>{i + 1}.</strong> {formatted}
                </div>
                """, unsafe_allow_html=True)

                if st.button(f"❌ Remove {i + 1}", key=f"remove_{i}"):
                    st.session_state.edit_availability.pop(i)
                    st.rerun()

            except Exception as e:
                st.warning(f"Invalid interval: {interval}")

        # --- Save availability
        if st.button("💾 Save Availability"):
            try:
                user_data = get_user_data(st.session_state.user_id)
                if not user_data:
                    st.error("Failed to fetch user data. Cannot update availability.")
                    return

                payload = {
                    "name": user_data.get("name"),
                    "phone": user_data.get("phone"),
                    "email": user_data.get("email"),
                    "about_section": user_data.get("about_section", ""),
                    "available": st.session_state.edit_availability,
                    "subjects_to_teach": user_data.get("subjects_to_teach", []),
                    "hourly_rate": user_data.get("hourly_rate", 0),
                    "meetings": user_data.get("meetings", []),
                    "rating": user_data.get("rating", 0),
                }

                success = send_data(f"/teachers/{st.session_state.user_id}", payload, method="PUT")

                if success:
                    st.success("✅ Availability updated successfully!")
                else:
                    st.error("❌ Failed to update availability.")

            except Exception as e:
                logger.exception("Error updating availability.")
                st.error("An error occurred while updating availability.")

    # -------------------------
    # Edit Profile Section
    # -------------------------
    elif choice == "Edit Profile":
        st.subheader("🛠️ Edit Your Profile")

        try:
            user_id = st.session_state.user_id
            existing_data = fetch_data(f"/teachers/{user_id}")

            if not existing_data:
                st.error("Failed to load your profile.")
            else:
                # --- Extract existing values
                name = existing_data.get("name", "")
                about = existing_data.get("about_section", "")
                hourly_rate = existing_data.get("hourly_rate", 0.0)
                raw_subjects = existing_data.get("subjects_to_teach", [])
                phone = existing_data.get("phone", "")
                email = st.text_input("Email", value=existing_data.get("email", ""))
                # --- The master list of allowed subjects
                all_subjects = [
                    "Math", "Physics", "Chemistry", "Biology",
                    "English", "Computer Science"
                ]

                # --- Normalize your stored list to title-case
                default_subjects = [s.title() for s in raw_subjects if s]

                # --- Build the form
                updated_name = st.text_input("Full Name", value=name)
                updated_about = st.text_area("About Me", value=about)
                updated_rate = st.number_input(
                    "Hourly Rate (USD)",
                    min_value=0.0,
                    value=hourly_rate,
                    step=5.0
                )
                updated_phone = st.text_input("Phone Number", value=phone)
                updated_subjects = st.multiselect(
                    "Subjects to Teach",
                    options=all_subjects,
                    default=default_subjects
                )

                if st.button("Update Profile"):
                    # Map your title-cased picks back to whatever you store
                    # (here I convert them to lowercase; adjust if needed)
                    existing_data["subjects_to_teach"] = [s.lower() for s in updated_subjects]
                    existing_data["name"] = updated_name.strip()
                    existing_data["about_section"] = updated_about.strip()
                    existing_data["hourly_rate"] = updated_rate
                    existing_data["phone"] = updated_phone.strip()
                    existing_data["email"] = email.strip()

                    ok1 = send_data(f"/teachers/{user_id}", existing_data, method="PUT")
                    user_payload = {"email": email.strip()}
                    ok2 = send_data(f"/users/{user_id}", user_payload, method="PUT")
                    if ok1 and ok2:
                        # keep your session in sync
                        st.session_state["user_email"] = email.strip()
                        st.success("Profile (and login email) updated successfully!")
                    else:
                        st.error("Something went wrong updating your profile/email.")

        except Exception:
            logger.exception("Teacher profile update failed.")
            st.error("An unexpected error occurred.")

    # -------------------------
    # My Profile Section
    # -------------------------
    elif choice == "My Profile":
        st.subheader("📋 My Profile")

        try:
            user_id = st.session_state.get("user_id")
            teacher_data = fetch_data(f"/teachers/{user_id}")

            if teacher_data:
                st.markdown("### 👤 Personal Information")
                st.write(f"**Name:** {teacher_data.get('name', 'N/A')}")
                st.write(f"**Email:** {teacher_data.get('email', 'N/A')}")
                st.write(f"**Phone:** {teacher_data.get('phone', 'N/A')}")

                st.markdown("### 🧾 About Me")
                st.write(teacher_data.get("about_section", "_No info provided._"))

                st.markdown("### 📚 Subjects To Teach")
                subjects = teacher_data.get("subjects_to_teach", [])
                st.write(", ".join(subjects) if subjects else "_None listed._")

                st.markdown("### 💰 Hourly Rate & Rating")
                st.write(f"**Hourly Rate:** ${teacher_data.get('hourly_rate', 'N/A')}")
                st.write(f"**Rating:** {teacher_data.get('rating', 'N/A')} / 5")

                st.markdown("### 🕒 Availability")
                availability = teacher_data.get("available", [])
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
                            st.markdown(f"{i + 1}. {html}<br>", unsafe_allow_html=True)


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
