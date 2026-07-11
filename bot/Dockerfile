FROM python:3.12-slim

ENV PYTHONUTF8=1 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

WORKDIR /app/bot

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY bot/ ./

CMD ["python", "app.py"]
