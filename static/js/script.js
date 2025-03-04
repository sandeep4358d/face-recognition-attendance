document.addEventListener('DOMContentLoaded', function() {
    // Navigation
    const navLinks = document.querySelectorAll('nav a');
    const panels = document.querySelectorAll('.panel');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all links
            navLinks.forEach(link => link.classList.remove('active'));
            // Add active class to clicked link
            this.classList.add('active');
            
            // Hide all panels
            panels.forEach(panel => panel.classList.remove('active'));
            
            // Show the selected panel
            const targetPanelId = this.getAttribute('data-section');
            document.getElementById(targetPanelId).classList.add('active');
            
            // Load dashboard data if dashboard panel is selected
            if (targetPanelId === 'dashboard-panel') {
                loadDashboardData();
            }
        });
    });
    
    // Form submission - Capture Images
    const captureForm = document.getElementById('captureForm');
    const webcamContainer = document.getElementById('webcam-container');
    const webcamElement = document.getElementById('webcam');
    const progressFill = document.getElementById('progress-fill');
    const progressStatus = document.getElementById('progress-status');
    
    captureForm.addEventListener('submit', function(event) {
        event.preventDefault();
        
        const name = document.getElementById('name').value;
        const studentId = document.getElementById('id').value;
        
        if (!name || !studentId) {
            showNotification('Please enter both name and student ID', 'error');
            return;
        }
        
        // Show webcam container
        webcamContainer.classList.remove('hidden');
        
        // Access webcam
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(stream => {
                webcamElement.srcObject = stream;
                
                // Prepare for image capture
                captureImages(name, studentId, stream);
            })
            .catch(error => {
                showNotification('Error accessing camera: ' + error.message, 'error');
                webcamContainer.classList.add('hidden');
            });
    });
    
    function captureImages(name, studentId, stream) {
        let captureCount = 0;
        const totalCaptures = 10;
        
        progressStatus.textContent = 'Preparing to capture images...';
        
        // Start the capture sequence
        setTimeout(() => {
            const captureInterval = setInterval(() => {
                captureCount++;
                
                // Update progress
                const progress = (captureCount / totalCaptures) * 100;
                progressFill.style.width = `${progress}%`;
                progressStatus.textContent = `Capturing image ${captureCount} of ${totalCaptures}...`;
                
                // Send the data to the server
                captureAndSendImage(name, studentId, captureCount);
                
                // Check if we're done
                if (captureCount >= totalCaptures) {
                    clearInterval(captureInterval);
                    
                    // Clean up
                    stream.getTracks().forEach(track => track.stop());
                    webcamElement.srcObject = null;
                    webcamContainer.classList.add('hidden');
                    progressFill.style.width = '0%';
                    
                    // Reset form
                    captureForm.reset();
                    
                    // Show success message
                    showNotification('Images captured successfully!', 'success');
                }
            }, 800); // Capture an image every 800ms
        }, 1000); // Small delay before starting
    }
    
    function captureAndSendImage(name, studentId, imageCount) {
        // Create a canvas element to capture the current video frame
        const canvas = document.createElement('canvas');
        canvas.width = webcamElement.videoWidth;
        canvas.height = webcamElement.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(webcamElement, 0, 0, canvas.width, canvas.height);
        
        // Convert the canvas to a blob
        canvas.toBlob(blob => {
            // Create form data for the request
            const formData = new FormData();
            formData.append('name', name);
            formData.append('studentId', studentId);
            formData.append('imageCount', imageCount);
            formData.append('image', blob, `${name}_${imageCount}.jpg`);
            
            // Send the image to the server
            fetch('/capture_image', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .catch(error => {
                console.error('Error sending image:', error);
            });
        }, 'image/jpeg');
    }
    
    // Mark Attendance
    const markAttendanceBtn = document.getElementById('markAttendance');
    
    markAttendanceBtn.addEventListener('click', function() {
        // Show webcam container
        webcamContainer.classList.remove('hidden');
        
        // Update status
        progressStatus.textContent = 'Starting face recognition...';
        
        // Access webcam
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(stream => {
                webcamElement.srcObject = stream;
                
                // Animate progress bar
                let progress = 0;
                const progressInterval = setInterval(() => {
                    progress += 5;
                    progressFill.style.width = `${progress}%`;
                    
                    if (progress >= 100) {
                        clearInterval(progressInterval);
                        
                        // Capture image and send for recognition
                        progressStatus.textContent = 'Processing...';
                        
                        // Create a canvas element to capture the current video frame
                        const canvas = document.createElement('canvas');
                        canvas.width = webcamElement.videoWidth;
                        canvas.height = webcamElement.videoHeight;
                        const ctx = canvas.getContext('2d');
                        ctx.drawImage(webcamElement, 0, 0, canvas.width, canvas.height);
                        
                        // Convert the canvas to a blob
                        canvas.toBlob(blob => {
                            // Create form data for the request
                            const formData = new FormData();
                            formData.append('image', blob, 'attendance.jpg');
                            
                            // Send the image to the server
                            fetch('/mark_attendance', {
                                method: 'POST',
                                body: formData
                            })
                            .then(response => response.json())
                            .then(data => {
                                // Clean up
                                stream.getTracks().forEach(track => track.stop());
                                webcamElement.srcObject = null;
                                webcamContainer.classList.add('hidden');
                                progressFill.style.width = '0%';
                                
                                if (data.error) {
                                    showNotification(data.error, 'error');
                                } else if (data.name === 'Unknown') {
                                    showNotification('Face not recognized. Please try again or register first.', 'error');
                                } else {
                                    showNotification(`Attendance marked for ${data.name}`, 'success');
                                    
                                    // If dashboard is visible, refresh it
                                    if (document.getElementById('dashboard-panel').classList.contains('active')) {
                                        loadDashboardData();
                                    }
                                }
                            })
                            .catch(error => {
                                console.error('Error marking attendance:', error);
                                showNotification('Failed to process attendance', 'error');
                                
                                // Clean up
                                stream.getTracks().forEach(track => track.stop());
                                webcamElement.srcObject = null;
                                webcamContainer.classList.add('hidden');
                                progressFill.style.width = '0%';
                            });
                        }, 'image/jpeg');
                    }
                }, 50);
            })
            .catch(error => {
                showNotification('Error accessing camera: ' + error.message, 'error');
                webcamContainer.classList.add('hidden');
            });
    });
    
    // Dashboard functionality
    const refreshDashboardBtn = document.getElementById('refreshDashboard');
    const dateFilter = document.getElementById('dateFilter');
    
    refreshDashboardBtn.addEventListener('click', function() {
        loadDashboardData();
    });
    
    dateFilter.addEventListener('change', function() {
        loadDashboardData();
    });
    
    function loadDashboardData() {
        const period = dateFilter.value;
        
        // Show loading state
        document.getElementById('attendanceList').innerHTML = '<tr><td colspan="5" class="text-center">Loading data...</td></tr>';
        
        // Get attendance data from the server
        fetch(`/get_attendance?period=${period}`)
            .then(response => response.json())
            .then(data => {
                updateDashboardStats(data.stats);
                updateAttendanceTable(data.records);
            })
            .catch(error => {
                console.error('Error loading dashboard data:', error);
                showNotification('Failed to load attendance data', 'error');
            });
    }
    
    function updateDashboardStats(stats) {
        // Update dashboard metrics
        document.getElementById('totalPresent').textContent = stats.totalPresent;
        document.getElementById('onTime').textContent = stats.onTime;
        document.getElementById('late').textContent = stats.late;
        document.getElementById('attendanceRate').textContent = stats.attendanceRate + '%';
    }
    
    function updateAttendanceTable(records) {
        const tableBody = document.getElementById('attendanceList');
        const noRecords = document.getElementById('noRecords');
        
        if (records.length === 0) {
            tableBody.innerHTML = '';
            noRecords.classList.remove('hidden');
            return;
        }
        
        noRecords.classList.add('hidden');
        
        // Clear the table
        tableBody.innerHTML = '';
        
        // Add each record to the table
        records.forEach(record => {
            const row = document.createElement('tr');
            
            // Create status class based on arrival time
            const statusClass = record.isLate ? 'status late' : 'status on-time';
            const statusText = record.isLate ? 'Late' : 'On Time';
            
            row.innerHTML = `
                <td>${record.studentId}</td>
                <td>${record.name}</td>
                <td>${record.date}</td>
                <td>${record.time}</td>
                <td><span class="${statusClass}">${statusText}</span></td>
            `;
            
            tableBody.appendChild(row);
        });
    }
    
    // Export functions
    document.getElementById('exportCSV').addEventListener('click', function() {
        const period = dateFilter.value;
        window.location.href = `/export_attendance?format=csv&period=${period}`;
    });
    
    document.getElementById('exportPDF').addEventListener('click', function() {
        const period = dateFilter.value;
        window.location.href = `/export_attendance?format=pdf&period=${period}`;
    });
    
    document.getElementById('printReport').addEventListener('click', function() {
        window.print();
    });
    
    // Notification system
    const notification = document.getElementById('notification');
    const notificationMessage = document.getElementById('notification-message');
    const closeNotification = document.getElementById('close-notification');
    
    function showNotification(message, type = 'info') {
        // Set message and color based on type
        notificationMessage.textContent = message;
        notification.className = 'notification';
    }
})