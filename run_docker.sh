docker image build -t elect:latest  .
docker container run --interactive --tty --rm -p 5000:5000 --name elect elect:latest
