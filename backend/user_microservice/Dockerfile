# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container
COPY . .

# Make port 8083 available to the world outside this container
ENV LISTEN_PORT=8083
EXPOSE 8083

# Define environment variable
ENV FLASK_APP=main.py

# Run app.py when the container launches
CMD ["python3", "main.py"]