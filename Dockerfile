FROM python:3.7

EXPOSE 80

WORKDIR /usr/src/app

RUN mkdir ~/.streamlit

COPY requirements.txt .//
#COPY config.toml ~/.streamlit/

RUN pip install -r requirements.txt

COPY . .
