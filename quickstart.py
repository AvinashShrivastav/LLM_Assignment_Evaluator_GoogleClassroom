import pandas as pd
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import pickle
import io
import googleapiclient.errors
from googleapiclient.http import MediaIoBaseDownload
from evalaute_submission import evaluate_submission
from pydantic import BaseModel
# Define the required scopes
SCOPES = [
    "https://www.googleapis.com/auth/classroom.courses",
    "https://www.googleapis.com/auth/classroom.coursework.me",
    "https://www.googleapis.com/auth/classroom.student-submissions.me.readonly",
    "https://www.googleapis.com/auth/classroom.student-submissions.students.readonly",
    "https://www.googleapis.com/auth/classroom.announcements.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


def main():
    """Fetch assignments and submissions from all courses."""
    creds = None

    # Check if token.pickle exists for cached credentials
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    # If no valid credentials, authenticate the user
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0, include_granted_scopes="true")

        # Save credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    # Build the Classroom API service
    classroom_service = build("classroom", "v1", credentials=creds)
    
    # Build the Drive API service for file downloads
    drive_service = build("drive", "v3", credentials=creds)

    # List courses
    results = classroom_service.courses().list(pageSize=10).execute()
    courses = results.get("courses", [])

    if not courses:
        print("No courses found.")
    else:
        print("Courses:")
        for course in courses:
            print(f"{course['name']} ({course['id']})")
            fetch_assignments_and_submissions(classroom_service, drive_service, course['id'])

def fetch_assignments_and_submissions(classroom_service, drive_service, course_id):
    """Fetch assignments and submissions for a given course."""
    
    # List all assignments (coursework) for the course
    coursework_results = classroom_service.courses().courseWork().list(courseId=course_id).execute()
    coursework = coursework_results.get("courseWork", [])
    if not coursework:
        print(f"No assignments found for course {course_id}.")
    else:
        print(f"Assignments for course {course_id}:")
        for assignment in coursework:
            print(f"  - {assignment['title']}")
            assignment_problem = assignment.get("description", "No description available")
            fetch_submissions(classroom_service, drive_service, course_id, assignment['id'], assignment_problem)

def fetch_submissions(classroom_service, drive_service, course_id, assignment_id, assignment_problem):
    """Fetch submissions for a given assignment."""
    # Prepare an empty list to store submission details
    submission_data = []

    # List student submissions for the assignment
    submissions_results = classroom_service.courses().courseWork().studentSubmissions().list(
        courseId=course_id,
        courseWorkId=assignment_id
    ).execute()
    
    submissions = submissions_results.get("studentSubmissions", [])
    
    if not submissions:
        print(f"  No submissions for assignment {assignment_id}.")
    else:
        print(f"  Submissions for assignment {assignment_id}:")
        for submission in submissions:
            student_id = submission['userId']
            submission_state = submission['state']
            print(f"    - {student_id} - {submission_state}")

            # Check if the submission contains the assignmentSubmission field with attachments
            if 'assignmentSubmission' in submission and 'attachments' in submission['assignmentSubmission']:
                for attachment in submission['assignmentSubmission']['attachments']:
                    file_id = attachment['driveFile']['id']
                    file_name = attachment['driveFile']['title']

                    # Download the attachment (PDF) for evaluation
                    submission_pdf = download_attachment(drive_service, file_id, file_name)

                    # Get grade and remarks using the evaluate_submission function
                    result = evaluate_submission(assignment_problem, submission_pdf)

                    # Add the submission details to the submission_data list
                    submission_data.append({
                        "Student ID": student_id,
                        "Submission State": submission_state,
                        "Grade": result.grade,
                        "Remarks": result.remarks,
                        "Strengths": result.strengths,
                        "Area of Improvement": result.area_of_improvement
                    })
        
                    # Save all submission details to an Excel file
                    save_to_excel(submission_data, assignment_id)

def download_attachment(drive_service, file_id, file_name):
    """Download an attachment from a student submission."""
    
    # Ensure the downloads directory exists
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
    
    try:
        # Request the file using the file ID from the Drive API
        request = drive_service.files().get_media(fileId=file_id)
        fh = io.FileIO(f"downloads/{file_name}", 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        print(f"Starting download of {file_name} (ID: {file_id})...")
        while done is False:
            status, done = downloader.next_chunk()
            print(f"  Downloading {file_name}... {int(status.progress() * 100)}% complete")

        print(f"  Downloaded {file_name} successfully.")
        return f"downloads/{file_name}"
    except googleapiclient.errors.HttpError as error:
        print(f"  An error occurred while downloading {file_name}: {error}")
        return None

def save_to_excel(submission_data, assignment_id):
    """Save the submission data to an Excel file."""
    if submission_data:
        df = pd.DataFrame(submission_data)
        excel_filename = f"submissions_{assignment_id}.xlsx"
        df.to_excel(excel_filename, index=False)
        print(f"  Submissions saved to {excel_filename}")
    else:
        print("  No submission data to save.")

if __name__ == "__main__":
    main()
