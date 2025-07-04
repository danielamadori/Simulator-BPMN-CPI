FROM python:3.13.2

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install "fastapi[standard]"
COPY src ./app/

EXPOSE 8001
CMD ["fastapi", "run", "app/main.py", "--port", "8001"]
