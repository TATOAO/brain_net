
# Start the project

Build
including observability
1. docker-compose -f docker/docker-compose.yml --profile observability build
2. docker-compose -f docker/docker-compose.yml --profile observability build --no-chache
3. docker-compose -f docker/docker-compose.yml build


Start
1. docker-compose -f docker/docker-compose.yml --profile observability up -d

Stop
1. docker-compose -f docker/docker-compose.yml --profile observability down
