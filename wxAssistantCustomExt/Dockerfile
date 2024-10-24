# Use an official Python runtime as a parent image
FROM --platform=linux/amd64 python:3.10 AS build

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy the the requirements files into the container
COPY requirements.txt /app

# # Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Copy remaining required files and folders to the container
COPY src/customExtension.py /app
#COPY content_files /app/content_files


# # Expose the port the app runs on
EXPOSE 5001

# Copy secrets to environment variables during build
RUN --mount=type=secret,id=secretfile1,target=/run/secrets/mysecrets \
    cp /run/secrets/mysecrets /app/.env

ENTRYPOINT [ "flask" ]
CMD ["run","--host=0.0.0.0"]