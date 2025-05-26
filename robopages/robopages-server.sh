#!/bin/bash
docker run -it --rm \
	-v/var/run/docker.sock:/var/run/docker.sock \  # Expose docker socket
	-v$PWD/pages:/root/.robopages \
	-v$PWD/data:/data \
	--network=host \
	dreadnode/robopages serve --lazy
