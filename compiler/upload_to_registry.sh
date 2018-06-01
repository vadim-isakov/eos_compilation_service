#!/bin/bash

AWS_REGISTRY=128894178443.dkr.ecr.eu-central-1.amazonaws.com
AWS_REGION=eu-central-1
BRANCH="$TRAVIS_BRANCH"
COMMIT="$(git log -1  --pretty=format:'%H')"
COMMIT_SHORT="$(git log -1  --pretty=format:'%h')"
GIT_TAG="$(git describe --tags)"
TAGS=( "latest" "branch_${BRANCH}" "commit_${COMMIT}" "commit_${COMMIT_SHORT}" "tag_${GIT_TAG}" )

# check if all images built
for NAME in "$@"
do
	if [ -z $(docker images -q "${NAME}:latest") ];
	then
		echo "docker image ${NAME}:latest does not exists!"
		exit 1
	fi
done

# upload images to registry
for NAME in "$@"
do
	for TAG in "${TAGS[@]}"
	do
		docker tag "${NAME}:latest" "${AWS_REGISTRY}/${NAME}:${TAG}"
		ecs-cli push --region "${AWS_REGION}" --ecs-profile travis "${AWS_REGISTRY}/${NAME}:${TAG}"
	done
done
