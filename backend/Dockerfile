FROM python:3.9-slim


# Prevents Python from writing .pyc files to disk and from buffering stdout and stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# apt-get: install dependencies
# install -y openscad
# rm -rf: clean up apt cache to reduce image size
RUN apt-get update && apt-get install -y \
    openscad \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]