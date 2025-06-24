#!/bin/bash

# # Start observability stack
# ./start-observability.sh start

# # Check status
# ./start-observability.sh status

# # View logs
# ./start-observability.sh logs jaeger

# # Clean up
# ./start-observability.sh clean

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Brain Net Observability Stack${NC}"
echo "=================================="

# Function to check if a service is running
check_service() {
    if docker-compose --profile observability ps "$1" | grep -q "Up"; then
        echo -e "${GREEN}✓ $1 is running${NC}"
        return 0
    else
        echo -e "${RED}✗ $1 is not running${NC}"
        return 1
    fi
}

# Function to show service URLs
show_urls() {
    echo -e "\n${BLUE}📊 Observability Dashboard URLs:${NC}"
    echo "=================================="
    echo -e "${YELLOW}Jaeger UI:${NC}           http://localhost:16686"
    echo -e "${YELLOW}Prometheus:${NC}         http://localhost:9090"
    echo -e "${YELLOW}Grafana:${NC}            http://localhost:3001 (admin/admin)"
    echo -e "${YELLOW}OTel Collector:${NC}     http://localhost:55679 (zPages)"
    echo -e "${YELLOW}Kibana:${NC}             http://localhost:5601"
    echo ""
    echo -e "${BLUE}📡 OpenTelemetry Endpoints:${NC}"
    echo "=================================="
    echo -e "${YELLOW}OTLP gRPC:${NC}          localhost:4317"
    echo -e "${YELLOW}OTLP HTTP:${NC}          localhost:4318"
    echo -e "${YELLOW}Jaeger gRPC:${NC}        localhost:14250"
    echo -e "${YELLOW}Jaeger HTTP:${NC}        localhost:14268"
}

# Parse command line arguments
case "$1" in
    "start"|"up")
        echo -e "${BLUE}🚀 Starting observability stack...${NC}"
        docker-compose --profile observability up -d otel-collector jaeger
        
        echo -e "\n${BLUE}⏳ Waiting for services to be ready...${NC}"
        sleep 10
        
        echo -e "\n${BLUE}🔍 Checking service status...${NC}"
        check_service "jaeger"
        check_service "otel-collector"
        
        show_urls
        ;;
        
    "stop"|"down")
        echo -e "${BLUE}🛑 Stopping observability stack...${NC}"
        docker-compose --profile observability stop otel-collector jaeger
        ;;
        
    "restart")
        echo -e "${BLUE}🔄 Restarting observability stack...${NC}"
        docker-compose --profile observability restart otel-collector jaeger
        
        echo -e "\n${BLUE}⏳ Waiting for services to be ready...${NC}"
        sleep 10
        
        check_service "jaeger"
        check_service "otel-collector"
        
        show_urls
        ;;
        
    "status")
        echo -e "${BLUE}📊 Observability stack status:${NC}"
        check_service "jaeger"
        check_service "otel-collector"
        check_service "prometheus"
        check_service "grafana"
        
        show_urls
        ;;
        
    "logs")
        service=${2:-"otel-collector"}
        echo -e "${BLUE}📋 Showing logs for $service...${NC}"
        docker-compose --profile observability logs -f "$service"
        ;;
        
    "clean")
        echo -e "${YELLOW}⚠️  This will remove all observability data. Continue? (y/N)${NC}"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            echo -e "${BLUE}🧹 Cleaning up observability stack...${NC}"
            docker-compose --profile observability down -v
            docker volume rm docker_jaeger_data 2>/dev/null || true
            echo -e "${GREEN}✓ Cleanup complete${NC}"
        else
            echo -e "${BLUE}Cleanup cancelled${NC}"
        fi
        ;;
        
    *)
        echo -e "${BLUE}Usage:${NC}"
        echo "  $0 start|up      - Start observability services"
        echo "  $0 stop|down     - Stop observability services" 
        echo "  $0 restart       - Restart observability services"
        echo "  $0 status        - Check service status"
        echo "  $0 logs [service] - Show logs (default: otel-collector)"
        echo "  $0 clean         - Remove all observability data"
        echo ""
        echo -e "${BLUE}Examples:${NC}"
        echo "  $0 start         # Start Jaeger and OpenTelemetry Collector" 
        echo "  $0 logs jaeger   # Show Jaeger logs"
        echo "  $0 status        # Check all observability services"
        ;;
esac 