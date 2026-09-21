# DMLog Comprehensive Testing Suite

This directory contains the complete testing infrastructure for DMLog, designed to ensure reliability, security, and performance across all components.

## Test Structure

### 📁 Unit Tests (`/unit`)
- **Service Tests**: Test individual service modules in isolation
- **Utility Tests**: Test helper functions and utilities
- **Model Tests**: Test data models and schemas
- **Repository Tests**: Test data access layer

### 📁 Integration Tests (`/integration`)
- **API Endpoint Tests**: Test REST API endpoints
- **Database Tests**: Test database operations and migrations
- **WebSocket Tests**: Test real-time communication
- **External Service Tests**: Test third-party integrations

### 📁 End-to-End Tests (`/e2e`)
- **User Journey Tests**: Full user workflows
- **Cross-Browser Tests**: Multi-browser compatibility
- **Mobile Responsive Tests**: Mobile device testing
- **Performance Tests**: User experience performance

### 📁 Load Tests (`/load`)
- **Stress Tests**: System capacity under load
- **API Performance Tests**: Endpoint performance metrics
- **Concurrent User Tests**: Multi-user scenarios
- **Database Performance Tests**: Database load testing

### 📁 Security Tests (`/security`)
- **Authentication Tests**: Login and security flows
- **Authorization Tests**: Permission and access control
- **Injection Tests**: SQL injection and XSS prevention
- **Data Protection Tests**: Sensitive data handling

### 📁 Fixtures (`/fixtures`)
- **Test Data**: Sample data for testing
- **Mock Services**: External service mocks
- **Database Fixtures**: Test database setups
- **Configuration**: Test environment configs

### 📁 Utils (`/utils`)
- **Test Helpers**: Common testing utilities
- **Custom Assertions**: Specialized test assertions
- **Mock Factories**: Data generation for tests
- **Test Clients**: Custom test clients

## Running Tests

### Quick Start
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=source_code --cov-report=html

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```

### Test Categories
```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# End-to-end tests (requires setup)
pytest tests/e2e/ -v --browser=chromium

# Load tests
locust -f tests/load/locustfile.py

# Security tests
pytest tests/security/ -v
```

### Coverage and Reporting
```bash
# Generate coverage report
pytest --cov=source_code --cov-report=html --cov-report=term

# Generate detailed test report
pytest --html=test-report.html --self-contained-html

# Performance benchmarking
pytest tests/performance/ --benchmark-only
```

## Configuration

### Environment Setup
1. Copy `tests/fixtures/.env.test` to `.env`
2. Configure test database settings
3. Set up external service mocks
4. Install test dependencies

### Test Database
```bash
# Setup test database
python tests/utils/setup_test_db.py

# Reset test data
python tests/utils/reset_test_data.py
```

## Quality Standards

### Coverage Requirements
- **Unit Tests**: >90% line coverage
- **Integration Tests**: >80% endpoint coverage
- **E2E Tests**: >70% user journey coverage
- **Overall Coverage**: >85%

### Performance Benchmarks
- **API Response Time**: <200ms (95th percentile)
- **Database Queries**: <100ms average
- **WebSocket Latency**: <50ms
- **Page Load Time**: <2s

### Security Standards
- **Authentication**: All endpoints secured
- **Authorization**: Proper access controls
- **Data Validation**: Input sanitization
- **Rate Limiting**: DDoS protection

## CI/CD Integration

### GitHub Actions
- Automatic test runs on PR
- Coverage reporting
- Security scanning
- Performance regression detection

### Test Environments
- **Development**: Local testing
- **Staging**: Pre-production validation
- **Production**: Smoke tests only

## Troubleshooting

### Common Issues
1. **Database Connection**: Check test DB configuration
2. **External Services**: Ensure mocks are running
3. **Browser Tests**: Install required browsers
4. **Performance Tests**: Check system resources

### Debug Mode
```bash
# Run tests with debug output
pytest -v -s --tb=short

# Run specific test with debugging
pytest tests/unit/test_dice_service.py::TestDiceService::test_roll_dice -v -s
```

## Contributing

### Adding New Tests
1. Follow existing naming conventions
2. Use appropriate test categories
3. Include documentation
4. Update coverage reports

### Test Standards
- Use descriptive test names
- Test both success and failure cases
- Include edge cases
- Mock external dependencies

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Data Management**: Clean up test data after each test
3. **Mock Strategy**: Mock external services effectively
4. **Performance**: Keep tests fast and efficient
5. **Documentation**: Document complex test scenarios

For detailed testing guidelines and examples, see the individual test directories and their respective README files.