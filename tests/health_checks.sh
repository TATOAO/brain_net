echo "Checking health..."
curl -X GET http://localhost:8000/health

# Check Redis
echo "Checking Redis..."
curl -X GET http://localhost:8000/health/redis

# Check Neo4j
echo "Checking Neo4j..."
curl -X GET http://localhost:8000/health/neo4j

# Check Elasticsearch
echo "Checking Elasticsearch..."
curl -X GET http://localhost:8000/health/elasticsearch

# Check PostgreSQL  
echo "Checking PostgreSQL..."
curl -X GET http://localhost:8000/health/postgres