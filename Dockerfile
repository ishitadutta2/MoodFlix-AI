# MoodFlix AI — production image
FROM python:3.12-slim

WORKDIR /app

# System deps needed by Pillow (avatar processing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Uploaded avatars persist outside the image (mount a volume in production)
RUN mkdir -p static/uploads/avatars

ENV FLASK_ENV=production
EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "--timeout", "60", "app:app"]
