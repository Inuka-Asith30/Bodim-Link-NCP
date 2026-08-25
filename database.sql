CREATE DATABASE IF NOT EXISTS bodim_link_ncp;
USE bodim_link_ncp;

-- Users Table (Students, Owners, Admins)
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('student', 'owner', 'admin') NOT NULL,
    gender ENUM('male', 'female', 'other') NULL,
    phone VARCHAR(15) NULL,
    status ENUM('pending', 'verified', 'rejected') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Boardings Table
CREATE TABLE boardings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    owner_id INT NOT NULL,
    name VARCHAR(150) NOT NULL,
    location VARCHAR(100) NOT NULL,
    address TEXT NOT NULL,
    monthly_rent DECIMAL(10,2) NOT NULL,
    security_deposit DECIMAL(10,2) NOT NULL,
    gender_preference ENUM('male', 'female', 'any') NOT NULL,
    boarding_type VARCHAR(50) NOT NULL,
    description TEXT,
    total_rooms INT,
    available_seats INT,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Boarding Facilities (Amenities)
CREATE TABLE facilities (
    boarding_id INT NOT NULL,
    wifi BOOLEAN DEFAULT FALSE,
    meals BOOLEAN DEFAULT FALSE,
    laundry BOOLEAN DEFAULT FALSE,
    study_room BOOLEAN DEFAULT FALSE,
    hot_water BOOLEAN DEFAULT FALSE,
    parking BOOLEAN DEFAULT FALSE,
    security BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (boarding_id) REFERENCES boardings(id) ON DELETE CASCADE
);

-- Owner Verifications (Electricity Bills)
CREATE TABLE owner_verifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    owner_id INT NOT NULL,
    bill_image_path VARCHAR(255) NOT NULL,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Visit Requests
CREATE TABLE visit_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    boarding_id INT NOT NULL,
    request_date DATE NOT NULL,
    status ENUM('pending', 'accepted', 'rejected') DEFAULT 'pending',
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (boarding_id) REFERENCES boardings(id) ON DELETE CASCADE
);

-- Ratings and Feedback
CREATE TABLE reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    boarding_id INT NOT NULL,
    rating INT CHECK (rating >= 1 AND rating <= 5),
    feedback TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (boarding_id) REFERENCES boardings(id) ON DELETE CASCADE
);
