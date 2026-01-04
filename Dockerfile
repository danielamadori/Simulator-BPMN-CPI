FROM python:3.13.2

# Install graphviz
RUN apt-get update
RUN apt-get install graphviz -y

# Copy files
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install "fastapi[standard]"
RUN pip install jupyter notebook

COPY src .
COPY docker.env .env

# Open ports: 8001 for API, 8888 for Jupyter
EXPOSE 8001
EXPOSE 8888

# Start script that runs both FastAPI and Jupyter
CMD ["sh", "-c", "python main.py & jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser --allow-root --NotebookApp.token='' --NotebookApp.notebook_dir=/app"]
