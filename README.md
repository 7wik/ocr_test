# OCR Application with Flask and Google Cloud Vision API

## Overview

This project is an OCR (Optical Character Recognition) application built with Flask and Google's Cloud Vision API. The application features a basic UI and is Dockerized for easy deployment. The solution is hosted on an EC2 instance for demonstration purposes.

## Features

- **OCR Processing**: Utilizes Google's Cloud Vision API for accurate OCR results.
- **Basic UI**: A simple user interface for uploading and processing images.
- **Dockerized**: The application is containerized using Docker, making it easy to deploy and run in any environment.
- **Cloud Setup**: Deployed on an EC2 instance for live demonstration.

## Project Structure

- `application.py`: The main Flask application file.
- `templates/`: Directory containing HTML templates for the UI.
- `Dockerfile`: Docker configuration file to build the application image.
- `requirements.txt`: Python dependencies required for the project.

## Prerequisites

- Docker installed on your machine.
- AWS EC2 instance set up with Docker installed.
- Google Cloud account with Cloud Vision API enabled.

## Installation

1. **Clone the repository:**
   ```sh
   git clone https://github.com/yourusername/ocr-application.git
   cd ocr-application
   ```
2. **Build the Docker image:**
    ```
    docker buildx build --platform linux/amd64 -t ocr-application .
    ```
3. **Run the Docker container:**
    ```
    docker run -d -p 80:8000 ocr-application
    ```
## Demo
[This is the link to the demo](http://44.223.253.91/)