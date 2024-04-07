FROM python:3.9

# # Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any dependencies
RUN pip install -r requirements.txt

# Copy all the python files to the working directory
COPY . .

# ARG ENV_SERVICE_ACCOUNT_KEY
# ARG ENV_COOKIES

# RUN echo $ENV_SERVICE_ACCOUNT_KEY > service_account_key.txt
# RUN echo $ENV_COOKIES > cookies.txt

# RUN cp service_account_key.txt /tmp/service_account_key.txt
# RUN cp cookies.txt /tmp/cookies.txt

# # Set the environment variable using the contents of the file
# RUN export SERVICE_ACCOUNT_KEY=$(cat /tmp/service_account_key.txt) && \
#     echo "SERVICE_ACCOUNT_KEY=$SERVICE_ACCOUNT_KEY" >> /etc/environment

# RUN export COOKIES=$(cat /tmp/cookies.txt) && \
#     echo "COOKIES=$COOKIES" >> /etc/environment

# ENV SERVICE_ACCOUNT_KEY=$ENV_SERVICE_ACCOUNT_KEY
# ENV COOKIES=$ENV_COOKIES

# Specify the command to run on container start
CMD [ "python", "./app.py" ]