### Hello world
# test sandbox start execute
curl -X POST http://localhost:8002/execute -H "Content-Type: application/json" -d '{"code": "print(\"Hello, World!\")"}'

# test sandbox get execution result
curl -X GET http://localhost:8002/execution/b3206b31-6821-4f6a-9acb-67e047e782af

# test sandbox get configuration
curl -X GET http://localhost:8002/config

# test sandbox get health
curl -X GET http://localhost:8002/health

