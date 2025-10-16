# app/Dockerfile (Corrected)

# 1. Start with the Python base image
FROM python:3.11-slim

# 2. Set a neutral working directory
WORKDIR /code

# 3. Copy only the requirements file first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy your application code into a subdirectory
# This creates the /code/app structure that Python expects
COPY . /code/app

# 5. The command to run when the container starts
# Now, from the /code directory, Python can correctly find the 'app' package
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]