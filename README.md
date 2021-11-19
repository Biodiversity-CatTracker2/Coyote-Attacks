# PyGoN

Dynamic app: https://coyote.eastus.cloudapp.azure.com/

Static app: https://biodiversity-cattracker2.github.io/PyGoN/

```bash
$ DOCKER_BUILDKIT=1 docker-compose up --detach --build
$ bash entrypoint.sh  # drop certificate.crt and private.key in certs/ before running this
```
