# Use official Python image with Debian
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Fix GPG issues and install system dependencies for Chrome and Selenium
RUN apt-get update --allow-releaseinfo-change && \
    apt-get install -y --allow-unauthenticated \
    wget \
    gnupg \
    unzip \
    curl \
    xvfb \
    # Chrome dependencies
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    libu2f-udev \
    libvulkan1 \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Set Chrome binary path
ENV CHROME_BIN=/usr/bin/google-chrome

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Install Chrome Driver directly (avoid webdriver-manager downloads)
RUN CHROMEDRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE) && \
    wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip" && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/chromedriver && \
    rm /tmp/chromedriver.zip

# Create directories with proper permissions
RUN mkdir -p /tmp/chrome-user-data /tmp/chrome-cache /app/.wdm && \
    chmod 1777 /tmp && \
    chmod -R 777 /tmp/chrome-user-data /tmp/chrome-cache /app/.wdm

# Create a non-root user for security
RUN useradd -m -u 1000 scraper && \
    chown -R scraper:scraper /app && \
    chown -R scraper:scraper /tmp/chrome-user-data /tmp/chrome-cache

# Set environment variables for webdriver-manager
ENV WDM_LOG_LEVEL=0
ENV WDM_CACHE_ROOT=/tmp/chrome-cache

USER scraper

# Default command
CMD ["python", "get_allassetcap.py"] 