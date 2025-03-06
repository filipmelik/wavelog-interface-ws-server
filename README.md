# Wavelog hardware interface websocket proxy server
todo description, possibly with image on how this work

## How to develop
`cd` int project directory and issue `docker-compose up --build`

## How to build and push docker image using podman
`cd` int project directory and issue:

```commandline
podman manifest rm wavelog-proxy-server
podman manifest create wavelog-proxy-server
podman build --platform linux/amd64,linux/arm64,linux/arm64/v8 --manifest localhost/wavelog-proxy-server .
podman manifest inspect localhost/wavelog-proxy-server:latest
```

verify the built image works: `podman run --rm -p 7777:8000 localhost/wavelog-proxy-server`

push the image to dockerhub: `podman manifest push localhost/wavelog-proxy-server:latest docker://docker.io/donmoron/wavelog-proxy-server`

NOTE: When pushing into dockerhub, the `unexpected EOF` error pops up pretty frequently.
The only cure I know is to update podman and then try pushing the image again and again 
until it succeeds :(