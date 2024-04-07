FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any dependencies
RUN pip install -r requirements.txt

# Copy all the python files to the working directory
COPY . .

ARG ENV_SERVICE_ACCOUNT_KEY
ARG ENV_COOKIES

ENV SERVICE_ACCOUNT_KEY $ENV_SERVICE_ACCOUNT_KEY
ENV COOKIES $ENV_COOKIES

# Specify the command to run on container start
CMD [ "python", "./app.py" ]