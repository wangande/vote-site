#!/bin/bash

VERSION_ID=$1

if [ -z "$VERSION_ID" ]; then
	echo "usage ./build_se.sh VERSION_ID [v2]"
	exit 1
fi

V_VALUE=$(git tag | grep $VERSION_ID | wc -l)
if [ "$V_VALUE" -gt "0" ]; then
	echo "success $V_VALUE value"
else
	B_VALUE=$(git branch | grep $VERSION_ID | wc -l)
	if [ "$B_VALUE" -gt "0" ]; then
		echo "success $B_VALUE value"
	else
		echo "no such version tag or branch"
		exit 1
	fi
fi

git checkout $VERSION_ID
cp Dockerfile.se Dockerfile
cp .dockerignore.se .dockerignore
if [ $# -gt 1 ];then
	VIMG=$2
	docker build -t vote-site$VIMG:$VERSION_ID .
	docker push vote-site$VIMG:$VERSION_ID
else
	docker build -t vote-site:$VERSION_ID .
	docker push vote-site:$VERSION_ID
fi
git checkout master
