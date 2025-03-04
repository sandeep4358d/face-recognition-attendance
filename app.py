import os
import cv2
import numpy as np
import pandas as pd
import face_recognition
from flask import Flask, render_template, request, redirect, jsonify, send_file
from datetime import datetime, timedelta
import io
import base64
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Paths
TRAINING_DIR = "training_images"
ATTENDANCE_FILE = "attendance_records/attendance.csv"
TEMP_DIR = "temp_uploads"

# Ensure directories exist
os.makedirs(TRAINING_DIR, exist_ok=True)
os.makedirs("attendance_records", exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

# Handle single image upload for the new capture process
@app.route('/capture_image', methods=['POST'])
def capture_image():
    try:
        name = request.form['name']
        student_id = request.form['studentId']
        image_count = request.form['imageCount']
        
        # Get the image file
        image_file = request.files['image']
        
        # Create user directory if it doesn't exist
        user_dir = os.path.join(TRAINING_DIR, name)
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
        
        # Save the image
        image_path = os.path.join(user_dir, f"{student_id}_{image_count}.jpg")
        image_file.save(image_path)
        
        return jsonify({"success": True, "message": f"Image {image_count} saved for {name}"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# Recognize face and mark attendance with updated method
@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    try:
        # Get the image file from the request
        image_file = request.files['image']
        temp_path = os.path.join(TEMP_DIR, "attendance_temp.jpg")
        image_file.save(temp_path)
        
        # Load the image for face recognition
        img = face_recognition.load_image_file(temp_path)
        
        # Get face encodings
        face_locations = face_recognition.face_locations(img)
        
        if not face_locations:
            return jsonify({"error": "No face detected. Please try again."})
        
        unknown_encoding = face_recognition.face_encodings(img, face_locations)[0]
        
        # Compare with known faces
        name = "Unknown"
        student_id = ""
        
        # Get all training images
        for person in os.listdir(TRAINING_DIR):
            person_dir = os.path.join(TRAINING_DIR, person)
            
            # Skip if not a directory
            if not os.path.isdir(person_dir):
                continue
                
            # Check each image for this person
            for img_name in os.listdir(person_dir):
                img_path = os.path.join(person_dir, img_name)
                
                # Try to extract student ID from filename
                if "_" in img_name:
                    current_id = img_name.split("_")[0]
                else:
                    current_id = "Unknown"
                
                # Load image and get encodings
                try:
                    known_img = face_recognition.load_image_file(img_path)
                    known_encodings = face_recognition.face_encodings(known_img)
                    
                    if not known_encodings:
                        continue
                        
                    # Compare faces
                    match = face_recognition.compare_faces([known_encodings[0]], unknown_encoding)[0]
                    
                    if match:
                        name = person
                        student_id = current_id
                        break
                except Exception as e:
                    print(f"Error processing {img_path}: {e}")
            
            # Break the outer loop if we found a match
            if name != "Unknown":
                break
        
        # Record attendance if a face was recognized
        if name != "Unknown":
            mark_attendance_csv(name, student_id)
            
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        return jsonify({"name": name, "studentId": student_id})
    except Exception as e:
        return jsonify({"error": str(e)})

def mark_attendance_csv(name, student_id):
    now = datetime.now()
    time_str = now.strftime("%H:%M:%S")
    date_str = now.strftime("%Y-%m-%d")
    
    # Set a threshold time for determining late attendance
    late_threshold = "09:00:00"  # Customize as needed
    is_late = time_str > late_threshold
    
    # Create the attendance file if it doesn't exist
    if not os.path.exists(ATTENDANCE_FILE):
        df = pd.DataFrame(columns=['Name', 'StudentID', 'Date', 'Time', 'IsLate'])
        df.to_csv(ATTENDANCE_FILE, index=False)
    
    # Read the existing attendance file
    df = pd.read_csv(ATTENDANCE_FILE)
    
    # Check if the person has already been marked for today
    today_attendance = df[(df["Name"] == name) & (df["Date"] == date_str)]
    
    if today_attendance.empty:
        # Create a new entry
        new_record = {
            'Name': name, 
            'StudentID': student_id,
            'Date': date_str, 
            'Time': time_str,
            'IsLate': is_late
        }
        df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
        df.to_csv(ATTENDANCE_FILE, index=False)

# New endpoint to get attendance data for the dashboard
@app.route('/get_attendance', methods=['GET'])
def get_attendance():
    period = request.args.get('period', 'today')
    
    # Read the attendance file
    if not os.path.exists(ATTENDANCE_FILE):
        return jsonify({"records": [], "stats": get_empty_stats()})
    
    df = pd.read_csv(ATTENDANCE_FILE)
    
    if df.empty:
        return jsonify({"records": [], "stats": get_empty_stats()})
    
    # Filter by date range
    today = datetime.now().strftime("%Y-%m-%d")
    
    if period == 'today':
        filtered_df = df[df['Date'] == today]
    elif period == 'yesterday':
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        filtered_df = df[df['Date'] == yesterday]
    elif period == 'week':
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        filtered_df = df[df['Date'] >= week_ago]
    elif period == 'month':
        month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        filtered_df = df[df['Date'] >= month_ago]
    else:
        filtered_df = df
    
    # Process records for the response
    records = []
    for _, row in filtered_df.iterrows():
        records.append({
            'name': row['Name'],
            'studentId': row['StudentID'],
            'date': row['Date'],
            'time': row['Time'],
            'isLate': bool(row['IsLate'])
        })
    
    # Calculate stats
    stats = calculate_stats(filtered_df)
    
    return jsonify({"records": records, "stats": stats})

def calculate_stats(df):
    if df.empty:
        return get_empty_stats()
    
    total_present = df.shape[0]
    on_time = df[df['IsLate'] == False].shape[0]
    late = df[df['IsLate'] == True].shape[0]
    
    # Assuming there are 30 students in the class (update this as needed)
    total_students = 30
    attendance_rate = round((total_present / total_students) * 100, 1)
    
    return {
        'totalPresent': total_present,
        'onTime': on_time,
        'late': late,
        'attendanceRate': attendance_rate
    }

def get_empty_stats():
    return {
        'totalPresent': 0,
        'onTime': 0,
        'late': 0,
        'attendanceRate': 0
    }

# Export attendance data
@app.route('/export_attendance', methods=['GET'])
def export_attendance():
    period = request.args.get('period', 'today')
    format_type = request.args.get('format', 'csv')
    
    # Read and filter the attendance data
    if not os.path.exists(ATTENDANCE_FILE):
        return jsonify({"error": "No attendance records found"}), 404
    
    df = pd.read_csv(ATTENDANCE_FILE)
    
    if df.empty:
        return jsonify({"error": "No attendance records found"}), 404
    
    # Filter by date range
    today = datetime.now().strftime("%Y-%m-%d")
    
    if period == 'today':
        filtered_df = df[df['Date'] == today]
        period_str = "Today"
    elif period == 'yesterday':
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        filtered_df = df[df['Date'] == yesterday]
        period_str = "Yesterday"
    elif period == 'week':
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        filtered_df = df[df['Date'] >= week_ago]
        period_str = "Last 7 Days"
    elif period == 'month':
        month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        filtered_df = df[df['Date'] >= month_ago]
        period_str = "Last 30 Days"
    else:
        filtered_df = df
        period_str = "All Time"
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"attendance_{period}_{timestamp}"
    
    if format_type == 'csv':
        # Export as CSV
        csv_data = filtered_df.to_csv(index=False)
        output = io.StringIO()
        output.write(csv_data)
        
        # Create response
        mem_file = io.BytesIO()
        mem_file.write(output.getvalue().encode())
        mem_file.seek(0)
        output.close()
        
        return send_file(
            mem_file,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f"{filename}.csv"
        )
    
    elif format_type == 'pdf':
        # For PDF, we'll return a simplified CSV for now
        # In a production app, you would generate an actual PDF using a library like ReportLab
        # For simplicity in this example, we're returning CSV labeled as PDF
        csv_data = filtered_df.to_csv(index=False)
        output = io.StringIO()
        output.write(csv_data)
        
        # Create response
        mem_file = io.BytesIO()
        mem_file.write(output.getvalue().encode())
        mem_file.seek(0)
        output.close()
        
        return send_file(
            mem_file,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f"{filename}.csv"
        )
    
    else:
        return jsonify({"error": "Unsupported export format"}), 400

if __name__ == '__main__':
    app.run(debug=True)