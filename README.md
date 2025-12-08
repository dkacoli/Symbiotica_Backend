# The Backend - A Microservice Architecture


## Each service is isolated

Own code, models, database, dependencies, and Dockerfile.

## Separation of concerns

- main.py

- routes.py → API endpoints

- services.py → Business logic

- models.py → Data models

- database.py → Database connections

Dockerfile
requirements.txt

## API Gateway

Can route external requests to the correct microservice.

## Docker Compose

Makes it easy to run all microservices together.