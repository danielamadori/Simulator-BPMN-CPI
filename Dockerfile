FROM python:3.13.2

# Install graphivz
RUN apt-get update
RUN apt-get install graphviz -y

# Copy files
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install "fastapi[standard]"
COPY src .

# Open 8001 port
EXPOSE 8001

# Start server
CMD ["fastapi", "run", "main.py", "--port", "8001"]
