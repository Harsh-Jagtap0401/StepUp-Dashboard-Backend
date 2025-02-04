# StepUp Backend

This is the backend service for the StepUp project. It is built using Flask and SQLAlchemy, and it provides APIs for managing test results and user authentication.

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- MySQL database
- pip (Python package installer)

### Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/your-repo/stepup-backend.git
    cd stepup-backend
    ```

2. Create a virtual environment and activate it:
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

4. Configure the database connection in `app.py`:
    ```python
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://<username>:<password>@<host>/<database>'
    ```


### Running the Application

1. Start the Flask application:
    ```sh
    flask run
    ```

2. The application will be available at `http://127.0.0.1:5000/`.

## API Endpoints

### User Authentication

- **Signup**: `POST /user/signup`
- **Login**: `POST /user/login`
- **User Details**: `GET /user/details`

### Test Results

- **Upload Data**: `POST /upload`
- **Dashboard 1 Data**: `GET /api/dashboard1`
- **Dashboard 2 Data**: `GET /api/dashboard2`
- **Candidates Pass**: `GET /api/candidates/pass`
- **Candidates Fail**: `GET /api/candidates/fail`
- **Candidates In Progress**: `GET /api/candidates/in_progress`
- **Total Invites**: `GET /api/candidates/invited`
- **Participant Details**: `GET /api/participant-details`
