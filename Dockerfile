# Use the official Python image as a parent image
FROM python:3.12

# Set the working directory in the container to /app
WORKDIR /app

# Copy all the files from the current directory to /app in the container
COPY . .

# Install the required packages
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the app runs on
EXPOSE 5000

# Command to run your app
CMD ["gunicorn", "app:app"]