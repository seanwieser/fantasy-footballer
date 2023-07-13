#!/bin/bash

docker-compose down

if [[ $(docker ps -a -q) ]]; then
    docker rm -f $(docker ps -a -q)
fi

docker volume rm $(docker volume ls -q) || echo "No volumes to remove"
sudo pkill -u postgres || echo "No postgres port to kill"