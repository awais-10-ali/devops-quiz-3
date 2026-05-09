FROM python:3.10-slim

# Install basic tools
RUN apt-get update && apt-get install -y wget gnupg unzip curl

# Modern, secure way to add the Google Chrome key (no apt-key)
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub > /etc/apt/trusted.gpg.d/google.asc

# Add the Chrome repository
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'

# Install Chrome
RUN apt-get update && apt-get install -y google-chrome-stable && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory and install Python dependencies
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data for summarization
RUN python -m nltk.downloader punkt punkt_tab

# Copy the rest of the code
COPY app.py /app/

# Expose port and run
EXPOSE 7000
CMD ["python", "app.py"]
