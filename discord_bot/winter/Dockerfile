FROM python:3.8-slim-buster
WORKDIR /app
COPY ./requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY ./iemreader.py .
COPY ./token.config .
COPY ./w/config.yaml .
CMD ["python3", "iemdiscordbot.py", "config.yaml"]