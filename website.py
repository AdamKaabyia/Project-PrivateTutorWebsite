from header import render_authentication_page, render_header
from login_register_logout import *
from select_profile import render_profile_selection
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


def check_existing_profile(profile_type):
    """Check if a profile already exists for the user."""
    endpoint = f"/{'students' if profile_type == 'Student' else 'teachers'}/{st.session_state.user_id}"
    response = fetch_data(endpoint)
    return response is not None


def create_profile(profile_type):
    """Automatically create a profile if it doesn't exist."""
    user_id = st.session_state.user_id
    user_name = st.session_state.get("user_name", "Unknown User")
    user_email = st.session_state.get("user_email", "")

    if profile_type == "Student":
        payload = {
            "id": user_id,
            "name": user_name,
            "phone": "Unknown",
            "email": user_email,
            "about_section": "Default student profile",
            "available": [],
            "rating": 0,
            "subjects_interested_in_learning": ["General"],
            "meetings": [],
        }
        response = send_data("/students", data=payload)
        if response:
            st.success("Student profile created!")
        else:
            st.error("Failed to create student profile.")
    elif profile_type == "Teacher":
        payload = {
            "id": user_id,
            "name": user_name,
            "phone": "Unknown",
            "email": user_email,
            "about_section": "Default teacher profile",
            "available": [],
            "rating": 0,
            "subjects_to_teach": ["General"],
            "hourly_rate": 10,
            "meetings": [],
        }
        response = send_data("/teachers", data=payload)
        if response:
            st.success("Teacher profile created!")
        else:
            st.error("Failed to create teacher profile.")


def render_authentication_page():
    """Render the login and registration interface."""
    st.title("Welcome to the Scheduler")
    auth_action = st.radio("Login or Register", ["Login", "Register"], key="auth_action")

    email = st.text_input("Email", placeholder="Enter your email")
    password = st.text_input("Password", type="password", placeholder="Enter your password")

    # Additional registration fields
    full_name = st.text_input("Full Name", placeholder="Enter your full name") if auth_action == "Register" else None
    username = st.text_input("Username", placeholder="Choose a username") if auth_action == "Register" else None

    if st.button("Submit"):
        if handle_auth(auth_action, email, password, full_name, username):
            st.session_state.navigation = "profile_creation"  # Move to profile creation


def handle_auth(auth_action, email, password, full_name=None, username=None):
    """Handle authentication for login or registration."""
    if not email or not password:
        st.warning("Please fill in both email and password.")
        return False

    if auth_action == "Login":
        user_profile = login(email, password)
        if user_profile:
            update_session(user_profile)
            st.success(f"Welcome back, {user_profile.get('name', 'User')}!")
            return True
        else:
            st.error("Login failed. Please try again.")
    elif auth_action == "Register":
        if not full_name or not username:
            st.warning("Please complete all registration fields.")
            return False

        user_profile = register(full_name, username, email, password)
        if user_profile:
            update_session(user_profile)
            st.success(f"Welcome, {user_profile.get('name', 'User')}!")
            return True
        else:
            st.error("Registration failed. Please try again.")
    return False


def update_session(user_profile):
    """Update session state with user information."""
    st.session_state.user_id = user_profile.get("user_id")
    # get user by id by calling the endpoint Request URL
    # https://project-privatetutor.onrender.com/users/id/676823f1e3603040e08723a3
    # now we update the fields
    st.session_state.user_authenticated = True
    st.session_state.profile_type = None  # Reset profile type
    # Store additional information
    st.session_state.user_name = user_profile.get("name", "Unknown User")
    st.session_state.user_email = user_profile.get("email", "")


def render_profile_creation(): # here we can check if the profile exits if yes skip the function
    """Render profile creation for the logged-in user."""
    st.title("Create Your Profile")
    profile_type = st.radio("Select Your Role", ["Student", "Teacher"], key="profile_type_selection")

    phone = st.text_input("Phone", placeholder="Enter your phone number")
    about_section = st.text_area("About You", placeholder="Write something about yourself")

    # Allow user-friendly input of available time intervals
    st.write("**Available Time Intervals**")
    available_intervals = st.session_state.get("available_intervals", [])
    start_date = st.date_input("Select Start Date")
    start_time = st.time_input("Select Start Time")
    end_date = st.date_input("Select End Date")
    end_time = st.time_input("Select End Time")

    if st.button("Add Time Interval"):
        # Combine date and time into ISO format
        start_iso = datetime.combine(start_date, start_time).isoformat()
        end_iso = datetime.combine(end_date, end_time).isoformat()

        # Validate that end time is after start time
        if datetime.fromisoformat(end_iso) <= datetime.fromisoformat(start_iso):
            st.error("End time must be after start time!")
        else:
            available_intervals.append({"start": start_iso, "end": end_iso})
            st.session_state["available_intervals"] = available_intervals
            st.success(f"Time interval added: {start_iso} to {end_iso}")

    if available_intervals:
        st.write("**Current Available Time Intervals:**")
        for interval in available_intervals:
            st.write(f"{interval['start']} to {interval['end']}")

    # Role-specific fields
    if profile_type == "Student":
        subjects = st.text_area("Subjects You Want to Learn", placeholder="E.g., Math, Physics")
        if st.button("Create Student Profile"):
            create_student_profile(
                id=st.session_state.user_id,
                name=st.session_state.get("user_name"),
                phone=phone,
                email=st.session_state.get("user_email"),
                about_section=about_section,
                subjects_interested_in_learning=subjects.split(","),
                available_intervals=available_intervals
            )
    elif profile_type == "Teacher":
        subjects = st.text_area("Subjects You Can Teach", placeholder="E.g., Math, Physics")
        hourly_rate = st.number_input("Hourly Rate", min_value=0, step=1)
        if st.button("Create Teacher Profile"):
            create_teacher_profile(
                id=st.session_state.user_id,
                name=st.session_state.get("user_name"),
                phone=phone,
                email=st.session_state.get("user_email"),
                about_section=about_section,
                subjects_to_teach=subjects.split(","),
                hourly_rate=hourly_rate,
                available_intervals=available_intervals
            )

def create_student_profile(id, name, phone, email, about_section, subjects_interested_in_learning, available_intervals):
    """Send a request to create a student profile."""
    payload = {
        "id": id,
        "name": name,
        "phone": phone,
        "email": email,
        "about_section": about_section,
        "available": available_intervals,
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
    """Send a request to create a teacher profile."""
    payload = {
        "id": id,
        "name": name,
        "phone": phone,
        "email": email,
        "about_section": about_section,
        "available": available_intervals,
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

    st.header("Your Meetings")
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.error("No user ID found. Please log in again.")
        return

    meetings = fetch_user_meetings(user_id)

    if meetings:
        for meeting in meetings:
            st.write(f"**Subject**: {meeting['subject']}")
            st.write(f"**Location**: {meeting['location']}")
            st.write(f"**Start Time**: {meeting['start_time']}")
            st.write(f"**Finish Time**: {meeting['finish_time']}")
            st.write(f"**Participants**: {', '.join(meeting['people'])}")
            st.markdown("---")
    else:
        st.info("You have no scheduled meetings.")



if __name__ == "__main__":
    main()
