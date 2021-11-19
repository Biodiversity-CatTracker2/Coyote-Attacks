FROM python:3.7

EXPOSE 80

WORKDIR /usr/src/app

RUN mkdir ~/.streamlit

COPY requirements.txt ./
COPY entrypoint.sh ./
#COPY config.toml ~/.streamlit/
RUN mkdir certs
ADD certs ./certs/

RUN pip install -r requirements.txt
RUN chmod +x entrypoint.sh
RUN ./entrypoint.sh

COPY . .
