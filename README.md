# Face Recognition-Based Attendance System

This is a **Face Recognition-Based Attendance System** that automates attendance marking using facial recognition. The system captures images, trains a model, and recognizes faces to mark attendance.

## Features
- **Face Registration:** Capture and store multiple images for training.
- **Face Recognition:** Detects and identifies students using face encodings.
- **Attendance Marking:** Logs attendance with timestamps and checks for late entries.
- **Attendance Reports:** View attendance records for today, yesterday, week, or month.
- **Export Data:** Download attendance records in CSV format.

## Tech Stack
- **Backend:** Flask
- **Frontend:** HTML, CSS, JavaScript
- **Face Recognition:** OpenCV, dlib, face_recognition
- **Database:** CSV-based storage (Pandas)

## Installation
1. Clone the repository:
   ```sh
   git clone https://github.com/yourusername/face-recognition-attendance.git
   ```
2. Navigate to the project folder:
   ```sh
   cd face-recognition-attendance
   ```
3. Create a virtual environment (optional but recommended):
   ```sh
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```
4. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
5. Run the application:
   ```sh
   python app.py
   ```

## Usage
1. Open `http://127.0.0.1:5000/` in your browser.
2. Register a student by capturing multiple images.
3. Upload an image to mark attendance.
4. View attendance records and export data if needed.

## Folder Structure
```
📂 face-recognition-attendance
│-- 📂 training_images        # Stores images for training
│-- 📂 attendance_records     # Stores attendance CSV files
│-- 📂 temp_uploads           # Stores temporary images
│-- app.py                    # Main Flask application
│-- requirements.txt          # Dependencies
│-- templates/index.html      # Frontend UI
│-- static/                   # CSS, JavaScript files
│-- README.md                 # Project documentation
```

## Dependencies
- Flask
- OpenCV
- face_recognition
- NumPy
- Pandas
- Werkzeug

Install dependencies using:
```sh
pip install -r requirements.txt
```

## Contributing
Feel free to fork the repo, make improvements, and submit a pull request!

## License
This project is licensed under the MIT License.
