FROM python:3.9-slim-bullseye

WORKDIR /app

# Install system dependencies and browsers
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    postgresql-client \
    libnss3 \
    libgbm1 \
    libgtk-3-0 \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libx11-xcb1 \
    libxcb-dri3-0 \
    libdrm2 \
    libgbm1 \
    libxss1 \
    libxshmfence1 \
    libglib2.0-0 \
    libnss3 \
    libcups2 \
    libdbus-1-3 \
    xdg-utils \
    libpango-1.0-0 \
    libcairo2 \
    fonts-liberation \
    libxkbcommon0 \
    libatspi2.0-0 \
    libexpat1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install chromium
RUN playwright install-deps

COPY . .
RUN chmod +x init.sh && sed -i 's/\r$//' init.sh

CMD ["./init.sh"]