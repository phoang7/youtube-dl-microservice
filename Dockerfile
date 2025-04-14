FROM python:3.12-alpine
WORKDIR /app
ENV FLASK_APP=services/youtube_dl.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV YOUTUBE_OUTPUT=/downloads
RUN apk add --no-cache gcc musl-dev linux-headers
RUN apk update
RUN apk upgrade
RUN apk add --no-cache ffmpeg
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
EXPOSE 5000
COPY . .
CMD ["flask", "run", "--debug"]