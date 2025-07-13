#!/bin/bash

if ! docker --version; then
	echo "Docker isn't installed"
	sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi

if ! docker compose version; then
	echo "Docker compose isn't installed"
	sudo apt-get update
	sudo apt-get install docker-compose-plugin
fi

sudo adduser --system --home /home/Docker docker
sudo chmod 700 /home/Docker
