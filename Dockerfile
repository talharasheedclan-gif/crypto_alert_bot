# Python slim image
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY src /app/src
COPY tradingview /app/tradingview

ENV PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["python", "-m", "src.main"]
