# bellman-request-system
This project is a real-time request management system designed to streamline communication between hotel operators and bellmen. The system allows the hotel operator to assign bellmen to rooms for assistance with luggage and other services, ensuring smooth and efficient service for guests. Note: the App is in beginner stage!

Key Features:

    Room Requests: Operators can add room requests for bellmen when guests need assistance.
    Real-Time Updates: Both operators and bellmen can see updates in real-time as requests are created, marked as in-progress, or completed. The page refreshes automatically without requiring manual reloads.
    In-Progress and Finished Requests: Requests can be marked as "In Progress" (red color) or "Finished," and finished requests can be stored and viewed on a separate page.
    Clear Finished Requests: Operators have the option to clear all finished requests with a confirmation prompt.
    User-Friendly Interface: The system uses a clean, dark-themed interface with easy-to-understand buttons for managing room requests.
    Real-Time Communication: Powered by Flask-SocketIO, ensuring that all connected clients see the same real-time data without needing to refresh the page.

Technologies Used:

    Python (Flask, Flask-SocketIO, SQLAlchemy)
    SQLite for database management
    HTML, CSS, JavaScript for the front-end
    Socket.IO for real-time communication

This system is intended to improve communication and coordination in hotels, making the work of operators and bellmen more efficient, while providing better service to guests..
