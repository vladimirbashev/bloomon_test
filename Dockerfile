FROM python:latest
WORKDIR /app
COPY parser.py .
CMD ["python", "parser.py"]