
FROM python:3.9-slim

RUN apt-get update && apt-get install -y

WORKDIR /usr/src/app

COPY . .

RUN pip3 install --no-cache-dir -r requirements.txt

EXPOSE 8083

CMD ["python3", "main.py"]