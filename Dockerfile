FROM python:latest
WORKDIR /app
RUN pip install click
COPY parser.py .
CMD ["python", "parser.py"]