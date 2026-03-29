FROM python:3.11-slim

WORKDIR /app

# Copy everything first
COPY . .

# Then install
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "run.py"]
