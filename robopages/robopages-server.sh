#!/bin/bash
docker run -it --rm \
	-v/var/run/docker.sock:/var/run/docker.sock \
	-v$PWD/pages:/root/.robopages \
	-v hackthebot:/data \
	--network=host \
	--name robopages \
	dreadnode/robopages serve --lazy
