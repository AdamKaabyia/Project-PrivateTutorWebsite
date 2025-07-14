from login_register_logout import *
from server_requests import *
from student_view import student_view
from teacher_view import teacher_view
import streamlit as st
from datetime import datetime


def main():
    # Initialize session state variables
    if "user_id" not in st.session_state:
        st.session_state.update({
            "user_id": None,
            "user_authenticated": False,
            "profile_type": None,
            "navigation": "auth",  # Controls navigation state
        })

    # Render header
    render_header()

    # Handle navigation dynamically
    if st.session_state.navigation == "auth":
        render_authentication_page()
    elif st.session_state.navigation == "profile_creation":
        render_profile_creation()
    elif st.session_state.navigation == "main_app":
        render_main_app()


def render_header():
    """Render the application header with toggle and logout button."""
    st.title("Welcome to the Scheduler")
    if st.session_state.user_authenticated:
        col1, col2 = st.columns([6, 1])  # Adjust layout for toggle and logout button
        with col1:
            if st.session_state.profile_type:
                toggle_text = (
                    "Switch to Teacher" if st.session_state.profile_type == "Student" else "Switch to Student"
                )
                if st.button(toggle_text):
                    toggle_profile()
        with col2:
            if st.button("Logout"):
                logout()


def toggle_profile():
    """Toggle between student and teacher profiles, and create one if it doesn't exist."""
    new_profile_type = "Teacher" if st.session_state.profile_type == "Student" else "Student"

    # Check if the new profile exists
    if not check_existing_profile(new_profile_type):
        create_profile(new_profile_type)

    # Switch the profile
    st.session_state.profile_type = new_profile_type
    st.success(f"Switched to {new_profile_type} profile!")


def validate_and_convert_intervals(intervals):
    """Ensure all time intervals are dictionaries with ISO 8601 'start' and 'end' strings."""
    validated = []

    for item in intervals:
        if not isinstance(item, dict):
            continue  # skip if not a dictionary

        start = item.get("start")
        end = item.get("end")

        if isinstance(start, datetime) and isinstance(end, datetime):
            validated.append({
                "start": start.isoformat(),
                "end": end.isoformat()
            })
        elif isinstance(start, str) and isinstance(end, str):
            try:
                # Make sure the strings are valid ISO datetime strings
                datetime.fromisoformat(start)
                datetime.fromisoformat(end)
                validated.append({
                    "start": start,
                    "end": end
                })
            except ValueError:
                continue  # skip invalid string formats
        # else: skip silently if data is malformed
    return validated


def create_profile(profile_type):
    """Automatically create a profile if it doesn't exist."""
    user_id = st.session_state.user_id
    user_name = st.session_state.get("user_name", "Unknown User")
    user_email = st.session_state.get("user_email", "")
    phone = st.session_state.get("phone", "Unknown")
    about = st.session_state.get("about_section", "Default profile")

    raw_intervals = st.session_state.get("available_intervals", [])
    available_intervals = validate_and_convert_intervals(raw_intervals)

    if profile_type == "Student":
        payload = {
            "id": user_id,
            "name": user_name,
            "phone": phone,
            "email": user_email,
            "about_section": about,
            "available": available_intervals,
            "rating": 0,
            "subjects_interested_in_learning": st.session_state.get("subjects", ["General"]),
            "meetings": [],
        }

        # st.subheader("📦 Student Payload Debug")
        # st.json(payload)

        response = send_data("/students", data=payload)
        if response:
            st.success("Student profile created!")
        else:
            st.error("Failed to create student profile.")

    elif profile_type == "Teacher":
        payload = {
            "id": user_id,
            "name": user_name,
            "phone": phone,
            "email": user_email,
            "about_section": about,
            "available": available_intervals,
            "rating": 0,
            "subjects_to_teach": st.session_state.get("subjects", ["General"]),
            "hourly_rate": st.session_state.get("rate", 10),
            "meetings": [],
        }

        # st.subheader("📦 Teacher Payload Debug")
        # st.json(payload)

        response = send_data("/teachers", data=payload)
        if response:
            st.success("Teacher profile created!")
        else:
            st.error("Failed to create teacher profile.")


def render_authentication_page():
    """Render the login and registration interface."""
    # If already authenticated, show greeting + Continue button
    if st.session_state.get("user_authenticated", False):
        # Check whether they just registered:
        is_new = st.session_state.pop("just_registered", False)
        if is_new:
            st.success(f"Welcome, {st.session_state.get('user_name','User')}!")
        else:
            st.success(f"Welcome back, {st.session_state.get('user_name','User')}!")

        if st.button("Continue"):
            # Figure out which profile they have (if any):
            if check_existing_profile("Student"):
                st.session_state.profile_type = "Student"
            elif check_existing_profile("Teacher"):
                st.session_state.profile_type = "Teacher"
            else:
                st.session_state.navigation = "profile_creation"
                st.rerun()

            # Now go into the main app
            st.session_state.navigation = "main_app"
            st.rerun()
        return

    # …otherwise show the login/register form as before…
    auth_action = st.radio("Login or Register", ["Login", "Register"], key="auth_action")
    email = st.text_input("Email", placeholder="Enter your email")
    password = st.text_input("Password", type="password", placeholder="Enter your password")
    full_name = st.text_input("Full Name", placeholder="Enter your full name") if auth_action == "Register" else None
    username = st.text_input("Username", placeholder="Choose a username") if auth_action == "Register" else None

    if st.button("Submit"):
        success = handle_auth(auth_action, email, password, full_name, username)
        if success:
            # newly‐registered folks go create a profile, returners go straight in
            if auth_action == "Register":
                st.session_state.navigation = "profile_creation"
            else:
                st.session_state.navigation = "main_app"
            st.rerun()


def handle_auth(auth_action, email, password, full_name=None, username=None):
    """Handle authentication for login or registration."""
    if not email or not password:
        st.warning("Please fill in both email and password.")
        return

    if auth_action == "Login":
        user_profile = login(email, password)
        if user_profile:
            update_session(user_profile)
            st.session_state.temp_login_success = True
            st.rerun()
        else:
            st.error("Login failed. Please try again.")

    elif auth_action == "Register":
        if not full_name or not username:
            st.warning("Please complete all registration fields.")
            return

        user_profile = register(full_name, username, email, password)
        if user_profile:
            update_session(user_profile)
            st.session_state.just_registered = True
            return True
        else:
            st.error("Registration failed. Please try again.")


def update_session(user_profile):
    """Update session state with user information."""
    str_id = user_profile.get("user_id")
    st.session_state.user_id = str(str_id)
    print(f"printing str_id :-> {str_id}")  # Outputs the string ID

    # get user by id by calling the endpoint Request URL
    # https://project-privatetutor.onrender.com/users/id/676823f1e3603040e08723a3
    # now we update the fields
    st.session_state.user_authenticated = True
    st.session_state.profile_type = None  # Reset profile type
    # Store additional information
    user_data = get_user_data(st.session_state.user_id)
    st.session_state.user_name = user_profile.get("name", "User")
    st.session_state.user_email = user_data.get("email", "")


###################################################

def display_profile(profile):
    """Display user profile details in a readable format."""
    st.subheader("Profile Details")
    st.write(f"**Name:** {profile['name']}")
    st.write(f"**Email:** {profile['email']}")
    if profile.get('phone'):
        st.write(f"**Phone:** {profile['phone']}")
    if profile.get('about_section'):
        st.write(f"**About:** {profile['about_section']}")
    if profile.get('available_intervals'):
        st.write("**Available Intervals:**")
        for interval in profile['available_intervals']:
            st.write(f"From {interval['start']} to {interval['end']}")


def display_full_profile(profile: dict, role: str):
    """Nicely render a Student or Teacher profile in Streamlit."""
    st.markdown(f"### 📋 Your Current {role} Profile")
    st.write(f"**Name:** {profile.get('name', 'N/A')}")
    st.write(f"**Email:** {profile.get('email', 'N/A')}")
    st.write(f"**Phone:** {profile.get('phone', '_Not provided_')}")
    st.write(f"**About:** {profile.get('about_section', '_Not provided_')}")

    # Subjects & role-specific fields
    if role == "Teacher":
        st.write(f"**Hourly Rate:** ${profile.get('hourly_rate', 0):.2f}")
        st.write(f"**Rating:** {profile.get('rating', 0)} / 5")
        subs = profile.get("subjects_to_teach", [])
        st.write("**Subjects You Can Teach:**", ", ".join(subs) if subs else "_None listed_")
    else:
        subs = profile.get("subjects_interested_in_learning", [])
        st.write("**Subjects You Want to Learn:**", ", ".join(subs) if subs else "_None listed_")

    # Availability
    avail = profile.get("available", [])
    if avail:
        st.write("**Availability:**")
        for i, iv in enumerate(avail, start=1):
            try:
                start = datetime.fromisoformat(iv["start"])
                end = datetime.fromisoformat(iv["end"])
                start_fmt = start.strftime("%A, %B %d, %Y at %I:%M %p")
                end_fmt = end.strftime("%I:%M %p")
                st.markdown(f"> **{i}.** 📅 {start_fmt} → {end_fmt}")
            except:
                st.markdown(f"> **{i}.** 📅 {iv.get('start', '?')} → {iv.get('end', '?')}")
    else:
        st.write("**Availability:** _None set_")


def render_profile_creation():
    """Let the user either see their existing profile(s) or create a new one."""
    st.title("Create Your Profile")
    profile_type = st.radio("Select Your Role", ["Student", "Teacher"], key="profile_type_selection")

    # 1) if they already have this role, show it and offer to add the other
    existing = check_existing_profile(profile_type)
    if existing:
        # show it
        display_full_profile(existing, profile_type)

        # button to add the *other* role
        other = "Teacher" if profile_type == "Student" else "Student"
        if st.button(f"➕ Add {other} Role"):
            # switch the UI into creation mode for the other role
            st.session_state.profile_type_selection = other
            st.session_state.available_intervals = []
            st.rerun()
        return  # stop here

    # 2) otherwise, render the creation form for this role
    phone = st.text_input("Phone", placeholder="Enter your phone number")
    about = st.text_area("About You", placeholder="Write something about yourself")

    st.markdown("### 📅 Available Time Intervals")
    start_date = st.date_input("Start Date", key="start_date")
    start_time = st.time_input("Start Time", key="start_time")
    end_date = st.date_input("End Date", key="end_date")
    end_time = st.time_input("End Time", key="end_time")
    start_dt = datetime.combine(start_date, start_time)
    end_dt = datetime.combine(end_date, end_time)

    if "available_intervals" not in st.session_state:
        st.session_state.available_intervals = []

    if st.button("➕ Add Time Interval"):
        if end_dt <= start_dt:
            st.error("End time must be after start time.")
        else:
            st.session_state.available_intervals.append({
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat()
            })
            st.success("Interval added!")

    st.markdown("#### 🕒 Current Available Time Intervals:")
    for i, iv in enumerate(st.session_state.available_intervals, start=1):
        st.write(f"{i}. {iv['start']} → {iv['end']}")
        if st.button(f"Delete {i}", key=f"delete_{i}"):
            st.session_state.available_intervals.pop(i - 1)
            st.rerun()

    # common fields
    user_id = st.session_state.user_id
    user_name = st.session_state.user_name
    user_email = st.session_state.user_email

    # role-specific final inputs + create button
    if profile_type == "Student":
        subjects = st.text_area("Subjects You Want to Learn", placeholder="E.g., Math, Physics")
        if st.button("Create Student Profile"):
            create_student_profile(
                id=user_id,
                name=user_name,
                phone=phone,
                email=user_email,
                about_section=about,
                subjects_interested_in_learning=[s.strip() for s in subjects.split(",") if s.strip()],
                available_intervals=st.session_state.available_intervals
            )

    else:  # Teacher
        subjects = st.text_area("Subjects You Can Teach", placeholder="E.g., Math, Physics")
        hourly_rate = st.number_input("Hourly Rate", min_value=0, step=1)
        if st.button("Create Teacher Profile"):
            create_teacher_profile(
                id=user_id,
                name=user_name,
                phone=phone,
                email=user_email,
                about_section=about,
                subjects_to_teach=[s.strip() for s in subjects.split(",") if s.strip()],
                hourly_rate=hourly_rate,
                available_intervals=st.session_state.available_intervals
            )


def create_student_profile(id, name, phone, email, about_section, subjects_interested_in_learning, available_intervals):
    """Send a request to create a student profile."""

    # ✅ Validate intervals
    validated_intervals = validate_and_convert_intervals(available_intervals)

    payload = {
        "id": id,
        "name": name,
        "phone": phone,
        "email": email,
        "about_section": about_section,
        "available": validated_intervals,
        "rating": 0,
        "subjects_interested_in_learning": subjects_interested_in_learning,
        "meetings": [],
    }

    response = send_data("/students", data=payload)
    if response:
        st.session_state.profile_type = "Student"
        st.session_state.navigation = "main_app"
        st.success("Student profile created successfully!")
    else:
        st.error("Failed to create student profile. Please try again.")


def create_teacher_profile(id, name, phone, email, about_section, subjects_to_teach, hourly_rate, available_intervals):
    validated_intervals = validate_and_convert_intervals(available_intervals)
    payload = {
        "id": id,
        "name": name,
        "phone": phone,
        "email": email,
        "about_section": about_section,
        "available": validated_intervals,
        "rating": 0,
        "subjects_to_teach": subjects_to_teach,
        "hourly_rate": hourly_rate,
        "meetings": [],
    }
    response = send_data("/teachers", data=payload)
    if response:
        st.session_state.profile_type = "Teacher"
        st.session_state.navigation = "main_app"
        st.success("Teacher profile created successfully!")
    else:
        st.error("Failed to create teacher profile. Please try again.")


def render_main_app():
    """Render the main application interface."""
    st.title(f"Welcome to the {st.session_state.profile_type} Dashboard")

    if st.session_state.profile_type == "Student":
        student_view()
    elif st.session_state.profile_type == "Teacher":
        teacher_view()


if __name__ == "__main__":
    main()
