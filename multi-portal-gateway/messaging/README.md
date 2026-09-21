# DMLogn8n Message Queue System

A comprehensive, production-ready message queue system for the DMLogn8n multi-agent platform, providing unified messaging capabilities with support for multiple backends (RabbitMQ, Redis Streams, Apache Kafka).

## 🚀 Features

### Core Capabilities
- **Multi-Backend Support**: RabbitMQ, Redis Streams, and Apache Kafka backends
- **Unified Message Broker Abstraction**: Single API for all operations
- **Advanced Message Routing**: Topic-based routing with pattern matching
- **Message Persistence**: Configurable durability guarantees
- **Dead Letter Queues**: Robust error handling and message recovery
- **Exactly-Once Delivery**: Message ordering and duplicate prevention
- **Real-time Streaming**: Stream processing and analytics
- **Circuit Breaker Patterns**: Resilient producer/consumer operations
- **Comprehensive Monitoring**: Metrics, health checks, and alerting

### Message Types Supported
- Agent-to-agent communication
- Game state updates and events
- Dialogue system messages
- Combat engine events
- World simulation updates
- System monitoring and alerts
- User actions and notifications
- AI model requests and responses

### Advanced Features
- **Message Serialization**: JSON, Avro, Protobuf support
- **Compression & Encryption**: Optional message compression and encryption
- **Priority Queues**: Configurable message priorities
- **Delayed Messaging**: Time-based message delivery
- **Batch Processing**: Efficient bulk message handling
- **Stream Processing**: Real-time analytics and pattern matching

## 📁 Architecture

```
messaging/
├── message_broker.py          # Core message broker abstraction
├── router.py                   # Message routing and topic management
├── utils.py                    # Utility functions and helpers
├── monitoring.py               # Monitoring and metrics collection
├── producers/                  # Message producers
│   ├── agent_producer.py       # Agent communication producer
│   ├── game_producer.py        # Game event producer
│   └── system_producer.py      # System event producer
├── consumers/                  # Message consumers
│   ├── agent_consumer.py       # Agent message consumer
│   ├── dialogue_consumer.py    # Dialogue system consumer
│   └── combat_consumer.py      # Combat engine consumer
├── processors/                 # Message processing components
│   ├── message_processor.py    # Base processing framework
│   ├── batch_processor.py      # Batch message processing
│   └── stream_processor.py     # Real-time stream processing
├── backends/                   # Backend implementations
│   ├── rabbitmq_backend.py     # RabbitMQ adapter
│   ├── redis_backend.py        # Redis Streams adapter
│   └── kafka_backend.py        # Apache Kafka adapter
└── config/                     # Configuration files
    ├── rabbitmq.yaml           # RabbitMQ configuration
    ├── redis-streams.yaml      # Redis Streams configuration
    └── kafka.yaml              # Kafka configuration
```

## 🛠️ Installation

### Dependencies

```bash
# Core dependencies
pip install aiofiles aio-pika aioredis aiokafka psutil pyyaml

# Optional dependencies for advanced features
pip install msgpack snappy zstandard  # Serialization and compression
pip install prometheus-client           # Prometheus metrics
pip import cryptography              # Encryption support
```

### Backend-Specific Setup

#### RabbitMQ
```bash
# Install RabbitMQ server
sudo apt-get install rabbitmq-server

# Enable management plugin
rabbitmq-plugins enable rabbitmq_management

# Create user
rabbitmqctl add_user dmlogn8n your_password
rabbitmqctl set_permissions dmlogn8n ".*" ".*" ".*"
```

#### Redis (Streams)
```bash
# Install Redis server
sudo apt-get install redis-server

# Enable Redis Streams (Redis 5.0+)
# Edit /etc/redis/redis.conf to enable persistence if needed
```

#### Apache Kafka
```bash
# Download and extract Kafka
wget https://downloads.apache.org/kafka/2.8.0/kafka_2.13-2.8.0.tgz
tar -xzf kafka_2.13-2.8.0.tgz

# Start Zookeeper
bin/zookeeper-server-start.sh config/zookeeper.properties

# Start Kafka broker
bin/kafka-server-start.sh config/server.properties
```

## 📖 Quick Start

### Basic Usage

```python
import asyncio
from messaging.message_broker import MessageBroker
from messaging.producers.agent_producer import AgentProducer
from messaging.consumers.agent_consumer import AgentConsumer
from messaging.monitoring import get_monitoring_instance

async def main():
    # Initialize monitoring
    monitoring = get_monitoring_instance()
    await monitoring.start()

    # Create message broker with RabbitMQ backend
    broker = MessageBroker("rabbitmq", "messaging/config/rabbitmq.yaml")
    await broker.connect()

    # Create producer and consumer
    agent_producer = AgentProducer(broker, "agent_001")
    agent_consumer = AgentConsumer(broker, "agent_001")

    # Initialize producer and consumer
    await agent_producer.initialize()
    await agent_consumer.initialize()

    # Start consuming messages
    await agent_consumer.start_consuming()

    # Send a message
    await agent_producer.send_direct_message(
        recipient_id="agent_002",
        content={"message": "Hello from agent_001!"},
        priority=MessagePriority.NORMAL
    )

    # Keep running
    await asyncio.sleep(10)

    # Cleanup
    await agent_consumer.shutdown()
    await agent_producer.shutdown()
    await broker.disconnect()
    await monitoring.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

### Game Events Example

```python
from messaging.producers.game_producer import GameProducer
from messaging.message_broker import MessageType

async def game_example():
    broker = MessageBroker("kafka", "messaging/config/kafka.yaml")
    await broker.connect()

    game_producer = GameProducer(broker, "game_001")
    await game_producer.initialize()

    # Add players
    await game_producer.add_player(PlayerInfo(
        player_id="player_001",
        name="Alice",
        character_id="char_001",
        location="town_square"
    ))

    # Publish player action
    await game_producer.publish_player_action(PlayerAction(
        action_id="action_001",
        player_id="player_001",
        action_type=ActionType.MOVE,
        target="forest_entrance",
        location="town_square"
    ))

    await broker.disconnect()
```

### Stream Processing Example

```python
from messaging.processors.stream_processor import TimeWindowStreamProcessor
from messaging.utils import TimedOperation

async def stream_example():
    processor = TimeWindowStreamProcessor(
        processor_id="event_processor",
        window_size=60.0  # 1-minute windows
    )
    await processor.initialize()

    # Add a simple pattern detector
    def high_frequency_detector(pattern_id, messages):
        if len(messages) > 100:
            return True  # Alert on high frequency
        return False

    # Process stream
    async def message_generator():
        for i in range(200):
            message = Message(
                type=MessageType.SYSTEM_ALERT,
                topic="system.alerts.warning",
                payload={"event_id": i, "value": i}
            )
            await processor.process_message(message)
            await asyncio.sleep(0.01)

    await message_generator()
    await processor.shutdown()
```

## 🔧 Configuration

### Environment Configuration

The system supports environment-specific configuration overrides:

```yaml
# In your config files
environments:
  development:
    rabbitmq:
      host: "localhost"
      port: 5672
      username: "dev_user"

  production:
    rabbitmq:
      host: "prod-rabbitmq.example.com"
      port: 5672
      ssl_enabled: true
      heartbeat: 300
```

### Backend Selection

Choose your backend based on requirements:

- **RabbitMQ**: Best for complex routing, flexible messaging patterns
- **Redis Streams**: Best for high-throughput, simple use cases
- **Kafka**: Best for high-volume event streaming and log aggregation

### Performance Tuning

#### RabbitMQ
```yaml
rabbitmq:
  publisher_confirms: true
  batch_size: 16384
  heartbeat: 600
  connection_timeout: 30
```

#### Redis Streams
```yaml
redis:
  stream_max_len: 10000
  consumer_batch_size: 10
  lag_check_interval: 10
```

#### Kafka
```yaml
kafka:
  compression_type: "snappy"
  acks: "all"
  batch_size: 32768
  linger_ms: 5
  enable_idempotence: true
```

## 📊 Monitoring and Observability

### Metrics Collection

The system automatically collects metrics for:
- Message throughput and latency
- Error rates and retry counts
- Consumer lag and processing times
- System resource usage
- Backend-specific metrics

### Health Checks

Built-in health checks monitor:
- Backend connectivity
- Consumer group health
- System resource availability
- Message queue depth

### Alerting

Configure alerts for:
- High error rates
- Consumer lag thresholds
- System resource limits
- Backend failures

Example alert rule:
```python
def high_error_rate(metrics):
    total_errors = metrics.get_counter_value("messages_failed")
    total_messages = metrics.get_counter_value("messages_processed")
    return total_messages > 0 and (total_errors / total_messages) > 0.05

alert_manager.add_alert_rule(
    "high_error_rate",
    high_error_rate,
    AlertSeverity.ERROR,
    "Error rate exceeded 5%"
)
```

## 🔒 Security

### Authentication and Authorization

#### RabbitMQ
```yaml
rabbitmq:
  username: "secure_user"
  password: "secure_password"
  ssl_enabled: true
```

#### Kafka
```yaml
kafka:
  security_protocol: "SASL_SSL"
  sasl_mechanism: "SCRAM-SHA-256"
  sasl_username: "kafka_user"
  sasl_password: "kafka_password"
```

### Message Encryption

```python
from cryptography.fernet import Fernet

# Generate encryption key
key = Fernet.generate_key()

# Create broker with encryption
broker = MessageBroker("rabbitmq", "config.yaml", encryption_key=key)
```

## 🧪 Testing

### Unit Tests

```python
import pytest
from messaging.message_broker import Message, MessageType

def test_message_creation():
    message = Message(
        type=MessageType.AGENT_COMMUNICATION,
        topic="test.topic",
        payload={"test": "data"}
    )
    assert message.id is not None
    assert message.type == MessageType.AGENT_COMMUNICATION
```

### Integration Tests

```python
async def test_producer_consumer_flow():
    broker = MessageBroker("redis", "test_config.yaml")
    await broker.connect()

    producer = AgentProducer(broker, "test_agent")
    consumer = AgentConsumer(broker, "test_agent")

    await producer.initialize()
    await consumer.initialize()
    await consumer.start_consuming()

    # Test message flow
    success = await producer.send_direct_message(
        "test_agent",
        {"test": "message"}
    )
    assert success

    # Allow time for processing
    await asyncio.sleep(1)

    await consumer.shutdown()
    await producer.shutdown()
    await broker.disconnect()
```

### Load Testing

```python
async def load_test():
    broker = MessageBroker("kafka", "load_test_config.yaml")
    await broker.connect()

    producer = GameProducer(broker, "load_test_game")
    await producer.initialize()

    # Send 10,000 messages
    tasks = []
    for i in range(10000):
        task = producer.publish_player_action(PlayerAction(
            action_id=f"action_{i}",
            player_id="load_test_player",
            action_type=ActionType.MOVE
        ))
        tasks.append(task)

    results = await asyncio.gather(*tasks)
    success_count = sum(results)

    print(f"Sent {success_count}/{len(tasks)} messages successfully")

    await producer.shutdown()
    await broker.disconnect()
```

## 🚀 Production Deployment

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY messaging/ ./messaging/

CMD ["python", "-m", "messaging.main"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  dmlogn8n-messaging:
    build: .
    environment:
      - BACKEND=rabbitmq
      - RABBITMQ_HOST=rabbitmq
      - RABBITMQ_USERNAME=dmlogn8n
      - RABBITMQ_PASSWORD=secure_password
    depends_on:
      - rabbitmq
      - redis
      - kafka

  rabbitmq:
    image: rabbitmq:3-management
    environment:
      - RABBITMQ_DEFAULT_USER=dmlogn8n
      - RABBITMQ_DEFAULT_PASS=secure_password
    ports:
      - "5672:5672"
      - "15672:15672"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181

  kafka:
    image: confluentinc/cp-kafka:latest
    depends_on:
      - zookeeper
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    ports:
      - "9092:9092"
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dmlogn8n-messaging
spec:
  replicas: 3
  selector:
    matchLabels:
      app: dmlogn8n-messaging
  template:
    metadata:
      labels:
        app: dmlogn8n-messaging
    spec:
      containers:
      - name: messaging
        image: dmlogn8n/messaging:latest
        env:
        - name: BACKEND
          value: "kafka"
        - name: KAFKA_BOOTSTRAP_SERVERS
          value: "kafka-service:9092"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

## 🔍 Troubleshooting

### Common Issues

#### Connection Failures
```python
# Check backend connectivity
try:
    await broker.connect()
except ConnectionError as e:
    logger.error(f"Failed to connect: {e}")
    # Check backend service status
```

#### High Consumer Lag
```python
# Monitor consumer lag
from messaging.monitoring import get_monitoring_instance

monitoring = get_monitoring_instance()
alerts = monitoring.alert_manager.get_active_alerts()

for alert in alerts:
    if "consumer_lag" in alert.name.lower():
        print(f"High consumer lag detected: {alert.message}")
```

#### Memory Issues
```python
# Check system metrics
system_metrics = monitoring.system_monitor.get_current_metrics()
if system_metrics.memory_percent > 90:
    logger.warning("High memory usage detected")
    # Consider scaling or optimizing
```

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or use development config
broker = MessageBroker("rabbitmq", "config/rabbitmq.yaml")
config = await broker.load_config()
config['rabbitmq']['debug_mode'] = True
```

## 📚 API Reference

### MessageBroker Class

```python
class MessageBroker:
    def __init__(self, backend_type: str, config_path: str, encryption_key: Optional[bytes] = None)
    async def connect(self) -> None
    async def disconnect(self) -> None
    async def publish(self, message: Message, routing_key: str = "") -> bool
    async def consume(self, queue_config: ConsumerConfig, handler: AsyncMessageHandler) -> None
    async def declare_queue(self, queue_config: QueueConfig) -> bool
    async def declare_exchange(self, exchange_config: ExchangeConfig) -> bool
    async def bind_queue(self, queue: str, exchange: str, routing_key: str) -> bool
```

### Message Structure

```python
@dataclass
class Message:
    id: str
    type: MessageType
    topic: str
    payload: Dict[str, Any]
    headers: Dict[str, str]
    priority: MessagePriority
    timestamp: float
    expiration: Optional[float]
    retry_count: int
    max_retries: int
    encoding: MessageEncoding
    compressed: bool
    encrypted: bool
    correlation_id: Optional[str]
    reply_to: Optional[str]
    source: Optional[str]
    destination: Optional[str]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the troubleshooting guide
- Review the API documentation
- Join our Discord community

## 🎯 Roadmap

- [ ] Add support for additional backends (NATS, Pulsar)
- [ ] Implement distributed tracing
- [ ] Add GraphQL API for metrics
- [ ] Create web dashboard
- [ ] Add message replay functionality
- [ ] Implement schema registry integration
- [ ] Add support for message schemas
- [ ] Create CLI tools for management

---

**Built with ❤️ for the DMLogn8n multi-agent platform**