#!/bin/sh

FILE=ssl-proxy-linux-amd64

if [ -f "$FILE" ]; then
    echo "$FILE exists."
else
    curl -LJ "https://getbin.io/suyashkumar/ssl-proxy?os=linux" | tar xvz
fi

nohup ./ssl-proxy-linux-amd64 -cert certs/certificate.crt -key certs/private.key -from 0.0.0.0:443 -to 0.0.0.0:80 &
