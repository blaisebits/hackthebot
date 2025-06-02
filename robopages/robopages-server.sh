#!/bin/bash
docker run -it --rm \
	-v/var/run/docker.sock:/var/run/docker.sock \
	-v$PWD/pages:/root/.robopages \
	-v$PWD/data:/data \
	--network=host \
	-e WORKINGDIR=$PWD \
	dreadnode/robopages serve --lazy
