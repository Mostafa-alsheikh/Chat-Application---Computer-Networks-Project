# Multi-Client Chat Application

This project implements a multi-client chat application using socket programming, designed to allow multiple users to communicate with each other through a server-client architecture. The application includes private messaging, group messaging, message persistence, and a graphical user interface (GUI) for an intuitive user experience.

## Features

### Mandatory Features
1. **Server-Client Architecture**  
   The application follows a server-client model where the server handles multiple client connections simultaneously using multithreading. Each client communicates with the server to send and receive messages.

2. **Private Messaging**  
   Users can send private messages to specific users. These messages are visible only to the recipient, ensuring privacy.

3. **Group Messaging**  
   Users can participate in group conversations. Messages sent in group mode are broadcasted to all connected clients.

4. **Message Persistence**  
   All messages are stored in a database or file, allowing users to view their previous messages even after disconnecting and reconnecting to the server.

5. **Graphical User Interface (GUI)**  
   The client application includes a GUI built using Tkinter. The interface allows users to send and receive messages easily and provides a simple, user-friendly experience.

### Optional Features
1. **Connection Management (Bonus: 1 point)**  
   The application gracefully handles lost connections, notifying users when their connection to the server is lost.

2. **Scalability (Bonus: 1 point)**  
   The server is scalable and can handle up to 50-100 clients without significant performance degradation.

3. **Security (Bonus: 1 point)**  
   Basic security measures are implemented to prevent plain text transmission of data. Future versions may include message encryption.

4. **User-Friendly Interface (Grade: 1/10)**  
   The GUI is designed to be intuitive, featuring scrollable chat windows, clear status messages, and easy-to-use message input fields.

5. **Cross-Platform Compatibility (Grade: 1/10)**  
   The application is designed to run on multiple operating systems, including Windows, macOS, and Linux.

## Technologies Used
- **Python 3.x**: The programming language used to develop the application.
- **Socket Programming**: For server-client communication.
- **Tkinter**: For creating the GUI.
- **SQLite** (or any database/file system): For storing message persistence.
  
## Getting Started

### Prerequisites
To run this application, you need Python 3.x installed on your machine.

You can install the necessary Python packages using the following command:

```bash
pip install tkinter
