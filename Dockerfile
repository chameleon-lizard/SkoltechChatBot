# Use an official Python image as a base
FROM python:3.11-slim

# Set the working directory to /app
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY src /app/src
COPY data /app/data
COPY .env /app/.env
COPY main.py /app/main.py 
COPY bot.py /app/bot.py 
COPY start_bot.py /app/start_bot.py 

RUN mkdir -p /app/cache 

EXPOSE 8001

# Run the command to start the application
CMD ["python", "start_bot.py"]
