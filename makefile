local:
	sudo docker build -t "adb:latest" -f "dockerfile.quick" .
	sudo docker container prune -f
	sudo docker run -it -v $$(pwd)/persistence:/persistence -v $$(pwd)/persistence:/logs --env-file .env adb