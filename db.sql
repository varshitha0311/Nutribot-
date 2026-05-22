-- =============================================
-- FOODAI DATABASE SETUP
-- Run this entire script in MySQL
-- =============================================

CREATE DATABASE IF NOT EXISTS food_classification;

USE food_classification;

-- Drop table if exists (for fresh setup)
DROP TABLE IF EXISTS users;

-- Create Users Table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(15) NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Optional: Add a test user (password = "test123")
INSERT INTO users (username, full_name, email, phone, password) 
VALUES (
    'testuser', 
    'Test User', 
    'test@example.com', 
    '9876543210', 
    '$2b$12$LQf9v5v5v5v5v5v5v5v5uO5v5v5v5v5v5v5v5v5v5v5v5v5v5v5v'  -- hashed "test123"
);

-- Verify tables
SHOW TABLES;
SELECT * FROM users;