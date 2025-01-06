# Google Classroom Assignment Evaluator

This project automates the process of fetching, grading, and evaluating student submissions from Google Classroom. Using Google APIs, it retrieves assignments, submissions, and associated files, grades them using an AI model, and generates reports.

## Features

- **Fetch Courses**: Automatically lists all courses from your Google Classroom.
- **Retrieve Assignments**: Fetches all assignments and their details for each course.
- **Download Submissions**: Downloads student submissions (PDF format) for evaluation.
- **Automated Grading**: Grades submissions based on the assignment requirements using an AI-powered evaluation model.
- **Feedback Generation**: Provides feedback, including strengths, areas for improvement, and remarks.
- **Report Export**: Saves grading data to Excel files for further analysis.

## Requirements

### Python Packages
- `pandas`
- `google-api-python-client`
- `google-auth-httplib2`
- `google-auth-oauthlib`
- `PyPDF2`
- `langchain`
- `faiss-cpu`
- `pydantic`
- `groq`

### Setup
1. **Google API Setup**:
   - Enable the Google Classroom and Google Drive APIs.
   - Download your `credentials.json` file.

2. **Environment Variables**:
   - Set the `GROQ_API_KEY` in your environment for AI-based evaluation.

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Required Scopes
The following OAuth 2.0 scopes are used:
- `https://www.googleapis.com/auth/classroom.courses`
- `https://www.googleapis.com/auth/classroom.coursework.me`
- `https://www.googleapis.com/auth/classroom.student-submissions.me.readonly`
- `https://www.googleapis.com/auth/classroom.student-submissions.students.readonly`
- `https://www.googleapis.com/auth/classroom.announcements.readonly`
- `https://www.googleapis.com/auth/drive.readonly`

## How to Run

1. **Authenticate Google Account**:
   - On the first run, the script will guide you through authenticating your Google account and generating a `token.pickle` file for subsequent use.

2. **Execute the Script**:
   ```bash
   python main.py
   ```

3. **Process Flow**:
   - Lists courses.
   - Fetches assignments for each course.
   - Downloads student submissions for assignments.
   - Evaluates the submissions using an AI model.
   - Saves results to an Excel file.

## Key Functions

### `main()`
- Authenticates and initializes Google Classroom and Drive APIs.
- Fetches courses and processes assignments and submissions.

### `fetch_assignments_and_submissions()`
- Retrieves assignments for a given course.
- Fetches and evaluates submissions for each assignment.

### `fetch_submissions()`
- Downloads student submissions from Google Drive.
- Grades submissions and generates feedback using AI.
- Saves results to an Excel file.

### `download_attachment()`
- Downloads a student's submission file from Google Drive.

### `save_to_excel()`
- Exports submission data, including grades and feedback, to an Excel file.

### AI Evaluation Workflow
- **Building FAISS Index**: Parses and indexes submission content using the `CharacterTextSplitter` and `SentenceTransformerEmbeddings`.
- **Excerpts Retrieval**: Retrieves relevant excerpts for evaluation based on the assignment description.
- **Grading and Feedback**: Uses the Groq AI client to evaluate the submission and generate feedback.

### `evaluate_submission()`
- Combines the entire workflow of indexing, retrieval, and evaluation to grade student submissions.

## Directory Structure
```
project/
├── credentials.json          # Google API credentials
├── token.pickle              # Cached Google API credentials
├── downloads/                # Directory for downloaded files
├── faiss_index/              # Directory for FAISS index files
├── main.py                   # Main script
├── evaluate_submission.py    # AI evaluation logic
├── requirements.txt          # Python dependencies
```

## Outputs
- **Console Logs**: Detailed logs showing progress (e.g., courses fetched, assignments processed, submissions evaluated).
- **Excel Reports**: Saved in the format `submissions_<assignment_id>.xlsx` containing the following columns:
  - Student ID
  - Submission State
  - Grade
  - Remarks
  - Strengths
  - Areas of Improvement

## Notes
- Ensure valid Google API credentials are in place (`credentials.json`).
- Use the `GROQ_API_KEY` for AI model-based evaluation.
- Handle exceptions (e.g., missing files, invalid tokens) for a seamless experience.

## Future Enhancements
- Add support for real-time notifications of submission evaluations.
- Extend grading logic to handle non-PDF submissions.
- Integrate more advanced AI models for feedback.

## License
This project is licensed under the MIT License.

