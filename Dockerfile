# Use the standard, more compatible Python image
FROM python:3.11

# Set the working directory in the container
WORKDIR /app

# Upgrade pip to the latest version first
RUN pip install --upgrade pip

# Copy the dependencies file
COPY ./requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code
COPY . .

# The command to run the app is specified in docker-compose.yml