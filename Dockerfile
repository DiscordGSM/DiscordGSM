# For more information, please refer to https://aka.ms/vscode-docker-python
FROM nikolaik/python-nodejs:python3.9-nodejs16

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Set timezone
ENV TZ Canada/Eastern

# Install pip requirements
COPY requirements.txt .

WORKDIR /app
COPY . /app

USER root
RUN npm install -g gamedig
RUN python -m pip install -r requirements.txt

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["python3", "bot.py"]
