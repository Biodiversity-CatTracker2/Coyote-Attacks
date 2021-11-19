FROM python:3.7

EXPOSE 80

WORKDIR /usr/src/app

COPY requirements.txt ./
COPY entrypoint.sh ./

RUN mkdir certs
ADD certs ./certs/

RUN pip install -r requirements.txt
RUN chmod +x entrypoint.sh
RUN ./entrypoint.sh

COPY . .
