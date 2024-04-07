FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any dependencies
RUN pip install -r requirements.txt

# Copy all the python files to the working directory
COPY . .

ARG ENV

# write ENV to .env file
RUN echo "$ENV" > .env

# Specify the command to run on container start
CMD [ "python", "./app.py" ]