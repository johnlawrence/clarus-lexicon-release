# Use the official Python image from DockerHub
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Install system dependencies (e.g., gcc for compiling Python libraries)
RUN apt-get update && apt-get install -y --no-install-recommends gcc

# Copy the requirements.txt file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files into the container
COPY . .

# Expose the port the app will run on (default Flask port)
EXPOSE 5000

# Command to run the Flask app
CMD pwd && ls -l && python /usr/src/app/run.py
