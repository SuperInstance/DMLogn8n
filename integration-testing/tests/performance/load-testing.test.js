/**
 * Load Testing Suite for DMlogn8n
 *
 * This test suite validates system performance under various load conditions:
 * - Concurrent user connections and interactions
 * - WebSocket connection limits and message throughput
 * - Database performance under load
 * - API response times under stress
 * - Memory and CPU usage monitoring
 * - Scalability limits identification
 */

const request = require('supertest')
const { io } = require('socket.io-client')
const { TestEnvironment } = require('../../src/helpers/TestEnvironment')
const { PerformanceMonitor, testLogger } = require('../../src/utils/logger')
const { config } = require('../../config/test-config')
const { expect } = require('chai')
const autocannon = require('autocannon')
const { performance } = require('perf_hooks')

describe('Load Testing Suite', function() {
  this.timeout(config.timeouts.performance)

  let testEnv
  let perfMonitor
  let connections = []
  let metrics = {
    api: {},
    websocket: {},
    database: {},
    system: {}
  }

  before(async function() {
    this.timeout(120000)

    perfMonitor = new PerformanceMonitor('load-testing')
    perfMonitor.startTimer('load-test-setup')

    testEnv = new TestEnvironment({
      autoStart: true,
      useInMemoryDatabases: true,
      cleanupOnExit: true
    })

    await testEnv.initialize()
    await testEnv.waitForReady()

    // Seed data for testing
    await testEnv.seedData('users', 100)
    await testEnv.seedData('characters', 200)
    await testEnv.seedData('guilds', 10)

    perfMonitor.endTimer('load-test-setup')
  })

  after(async function() {
    this.timeout(60000)

    perfMonitor.startTimer('load-test-cleanup')

    // Close all connections
    for (const conn of connections) {
      if (conn && conn.disconnect) {
        conn.disconnect()
      }
    }

    await testEnv.cleanup()

    const summary = perfMonitor.getSummary()
    console.log('\n=== Load Testing Performance Summary ===')
    console.log(JSON.stringify(summary, null, 2))

    perfMonitor.endTimer('load-test-cleanup')
  })

  describe('API Load Testing', function() {
    it('should handle concurrent API requests', async function() {
      perfMonitor.startTimer('api-concurrent-requests')

      const concurrentUsers = 50
      const requestsPerUser = 10
      const endpoints = [
        { method: 'GET', path: '/api/status' },
        { method: 'GET', path: '/api/characters' },
        { method: 'GET', path: '/api/quests/available' },
        { method: 'GET', path: '/api/guilds' },
        { method: 'POST', path: '/api/auth/login', body: { email: 'test@test.com', password: 'test' } }
      ]

      const promises = []

      for (let user = 0; user < concurrentUsers; user++) {
        for (let req = 0; req < requestsPerUser; req++) {
          const endpoint = endpoints[Math.floor(Math.random() * endpoints.length)]
          const promise = request('http://localhost:5678')
            [endpoint.method.toLowerCase()](endpoint.path)
            .send(endpoint.body || {})
            .timeout(10000)

          promises.push(promise)
        }
      }

      const startTime = performance.now()
      const results = await Promise.allSettled(promises)
      const endTime = performance.now()

      const totalRequests = results.length
      const successfulRequests = results.filter(r => r.status === 'fulfilled').length
      const failedRequests = results.filter(r => r.status === 'rejected').length
      const totalTime = endTime - startTime
      const requestsPerSecond = (totalRequests / totalTime) * 1000
      const averageResponseTime = totalTime / totalRequests

      metrics.api.concurrent = {
        totalRequests,
        successfulRequests,
        failedRequests,
        successRate: (successfulRequests / totalRequests) * 100,
        totalTime,
        requestsPerSecond,
        averageResponseTime
      }

      testLogger.performance('api-concurrent-requests', requestsPerSecond, 'req/s', metrics.api.concurrent)

      expect(successfulRequests / totalRequests).to.be.above(0.95) // 95% success rate
      expect(requestsPerSecond).to.be.above(100) // Minimum 100 req/s

      perfMonitor.endTimer('api-concurrent-requests')
    })

    it('should maintain response times under increasing load', async function() {
      perfMonitor.startTimer('api-response-time-scaling')

      const loadLevels = [10, 25, 50, 100, 200, 500]
      const results = []

      for (const loadLevel of loadLevels) {
        const promises = []
        const startTime = performance.now()

        // Generate load
        for (let i = 0; i < loadLevel; i++) {
          promises.push(
            request('http://localhost:5678')
              .get('/api/characters')
              .timeout(15000)
          )
        }

        const loadResults = await Promise.allSettled(promises)
        const endTime = performance.now()

        const successful = loadResults.filter(r => r.status === 'fulfilled').length
        const totalTime = endTime - startTime
        const avgResponseTime = totalTime / loadLevel

        results.push({
          loadLevel,
          successful,
          totalTime,
          avgResponseTime,
          requestsPerSecond: (loadLevel / totalTime) * 1000
        })

        // Brief pause between load levels
        await new Promise(resolve => setTimeout(resolve, 2000))
      }

      metrics.api.responseTimeScaling = results

      testLogger.performance('api-scaling-results', results.length, 'load-levels', { results })

      // Validate that response times don't degrade excessively
      const lastResult = results[results.length - 1]
      const firstResult = results[0]
      const degradationFactor = lastResult.avgResponseTime / firstResult.avgResponseTime

      expect(degradationFactor).to.be.below(5) // Response time shouldn't increase by more than 5x
      expect(lastResult.successful / lastResult.loadLevel).to.be.above(0.90) // 90% success rate at highest load

      perfMonitor.endTimer('api-response-time-scaling')
    })

    it('should handle API stress testing with autocannon', async function() {
      perfMonitor.startTimer('api-stress-test')

      const result = await autocannon({
        url: 'http://localhost:5678/api/status',
        connections: 100,
        duration: 30, // seconds
        pipelining: 10,
        requests: [
          {
            method: 'GET',
            path: '/api/status'
          },
          {
            method: 'GET',
            path: '/api/characters'
          },
          {
            method: 'GET',
            path: '/api/quests/available'
          }
        ]
      })

      metrics.api.autocannon = {
        requests: result.requests,
        latency: result.latency,
        throughput: result.throughput,
        errors: result.errors,
        timeouts: result.timeouts,
        statusCodeStats: result.statusCodeStats,
        duration: result.duration
      }

      testLogger.performance('autocannon-requests', result.requests.total, 'total', result)
      testLogger.performance('autocannon-latency', result.latency.average, 'ms', result)

      expect(result.latency.average).to.be.below(1000) // Average latency under 1 second
      expect(result.throughput.average).to.be.above(50) // At least 50 req/s
      expect(result.errors).to.be.below(result.requests.total * 0.05) // Less than 5% errors

      perfMonitor.endTimer('api-stress-test')
    })
  })

  describe('WebSocket Load Testing', function() {
    it('should handle concurrent WebSocket connections', async function() {
      perfMonitor.startTimer('websocket-concurrent-connections')

      const connectionCounts = [10, 50, 100, 500, 1000]
      const connectionResults = []

      for (const count of connectionCounts) {
        const startTime = performance.now()
        const testConnections = []

        // Create connections
        for (let i = 0; i < count; i++) {
          const socket = io('http://localhost:5678', {
            transports: ['websocket'],
            forceNew: true
          })

          testConnections.push(socket)
        }

        // Wait for all connections to establish
        await Promise.all(
          testConnections.map(socket =>
            new Promise(resolve => {
              if (socket.connected) {
                resolve()
              } else {
                socket.on('connect', resolve)
              }
            })
          )
        )

        const connectionTime = performance.now() - startTime
        const connectedCount = testConnections.filter(s => s.connected).length

        connectionResults.push({
          connectionCount: count,
          connectedCount,
          connectionTime,
          successRate: (connectedCount / count) * 100
        })

        // Test message sending
        const messageStartTime = performance.now()
        const messagePromises = []

        for (const socket of testConnections) {
          if (socket.connected) {
            messagePromises.push(
              new Promise(resolve => {
                socket.emit('ping', { timestamp: Date.now() })
                socket.once('pong', resolve)
              })
            )
          }
        }

        await Promise.all(messagePromises)
        const messageTime = performance.now() - messageStartTime

        connectionResults[connectionResults.length - 1].messageTime = messageTime

        // Cleanup connections for next test
        testConnections.forEach(socket => socket.disconnect())
        await new Promise(resolve => setTimeout(resolve, 1000))
      }

      metrics.websocket.connections = connectionResults

      testLogger.performance('websocket-connections', connectionResults.length, 'test-runs', { results: connectionResults })

      // Validate connection handling
      const lastResult = connectionResults[connectionResults.length - 1]
      expect(lastResult.successRate).to.be.above(0.95) // 95% connection success rate
      expect(lastResult.messageTime).to.be.below(5000) // Messages should complete within 5 seconds

      perfMonitor.endTimer('websocket-concurrent-connections')
    })

    it('should handle high-frequency message throughput', async function() {
      perfMonitor.startTimer('websocket-message-throughput')

      const connectionCount = 100
      const messagesPerConnection = 50
      const connections = []
      const messageStats = {
        sent: 0,
        received: 0,
        errors: 0,
        totalLatency: 0
      }

      // Create connections
      for (let i = 0; i < connectionCount; i++) {
        const socket = io('http://localhost:5678', {
          transports: ['websocket']
        })

        socket.on('connect', () => {
          // Start sending messages
          for (let j = 0; j < messagesPerConnection; j++) {
            const startTime = performance.now()
            socket.emit('test-message', {
              id: `${i}-${j}`,
              timestamp: startTime,
              data: `test message ${j}`
            })

            messageStats.sent++
          }
        })

        socket.on('test-response', (data) => {
          const latency = performance.now() - data.timestamp
          messageStats.received++
          messageStats.totalLatency += latency
        })

        socket.on('error', () => {
          messageStats.errors++
        })

        connections.push(socket)
      }

      // Wait for all connections and messages
      await new Promise(resolve => setTimeout(resolve, 10000))

      // Calculate metrics
      const averageLatency = messageStats.totalLatency / messageStats.received
      const messageRate = messageStats.received / 10 // messages per second
      const errorRate = messageStats.errors / messageStats.sent

      metrics.websocket.throughput = {
        connections: connectionCount,
        messagesSent: messageStats.sent,
        messagesReceived: messageStats.received,
        errors: messageStats.errors,
        averageLatency,
        messageRate,
        errorRate
      }

      testLogger.performance('websocket-throughput', messageRate, 'msg/s', metrics.websocket.throughput)

      // Cleanup
      connections.forEach(socket => socket.disconnect())

      expect(messageStats.received / messageStats.sent).to.be.above(0.90) // 90% message delivery
      expect(averageLatency).to.be.below(100) // Average latency under 100ms
      expect(errorRate).to.be.below(0.05) // Less than 5% error rate

      perfMonitor.endTimer('websocket-message-throughput')
    })
  })

  describe('Database Performance Testing', function() {
    it('should handle concurrent database operations', async function() {
      perfMonitor.startTimer('database-concurrent-operations')

      const mongodb = testEnv.getDatabase('mongodb')
      const operationCounts = [100, 500, 1000, 5000]
      const dbResults = []

      for (const count of operationCounts) {
        const startTime = performance.now()
        const operations = []

        // Concurrent read operations
        for (let i = 0; i < count; i++) {
          operations.push(
            mongodb.collection('users').findOne({ _id: `test-user-${i % 10}` })
          )
        }

        // Concurrent write operations
        for (let i = 0; i < count / 10; i++) {
          operations.push(
            mongodb.collection('test_performance').insertOne({
              _id: `test-${Date.now()}-${i}`,
              data: `test data ${i}`,
              timestamp: new Date()
            })
          )
        }

        await Promise.all(operations)
        const endTime = performance.now()

        dbResults.push({
          operationCount: count,
          totalTime: endTime - startTime,
          operationsPerSecond: ((count + count / 10) / (endTime - startTime)) * 1000
        })

        // Cleanup test data
        await mongodb.collection('test_performance').deleteMany({})
      }

      metrics.database.concurrent = dbResults

      testLogger.performance('database-operations', dbResults.length, 'test-runs', { results: dbResults })

      // Validate database performance
      const lastResult = dbResults[dbResults.length - 1]
      expect(lastResult.operationsPerSecond).to.be.above(1000) // Minimum 1000 ops/sec

      perfMonitor.endTimer('database-concurrent-operations')
    })

    it('should handle complex query performance', async function() {
      perfMonitor.startTimer('database-complex-queries')

      const mongodb = testEnv.getDatabase('mongodb')
      const queryTypes = [
        {
          name: 'simple-find',
          query: () => mongodb.collection('characters').find({ level: { $gte: 5 } }).toArray()
        },
        {
          name: 'aggregation',
          query: () => mongodb.collection('characters').aggregate([
            { $match: { level: { $gte: 1 } } },
            { $group: { _id: '$class', avgLevel: { $avg: '$level' }, count: { $sum: 1 } } },
            { $sort: { count: -1 } }
          ]).toArray()
        },
        {
          name: 'text-search',
          query: () => mongodb.collection('characters').find({
            $text: { $search: 'dragon' }
          }).toArray()
        },
        {
          name: 'complex-lookup',
          query: () => mongodb.collection('characters').aggregate([
            { $lookup: { from: 'users', localField: 'userId', foreignField: '_id', as: 'user' } },
            { $unwind: '$user' },
            { $match: { 'user.roles': 'player' } },
            { $group: { _id: '$race', count: { $sum: 1 } } }
          ]).toArray()
        }
      ]

      const queryResults = []

      for (const queryType of queryTypes) {
        const iterations = 100
        const times = []

        for (let i = 0; i < iterations; i++) {
          const startTime = performance.now()
          await queryType.query()
          const endTime = performance.now()
          times.push(endTime - startTime)
        }

        const avgTime = times.reduce((a, b) => a + b, 0) / times.length
        const minTime = Math.min(...times)
        const maxTime = Math.max(...times)

        queryResults.push({
          queryType: queryType.name,
          iterations,
          avgTime,
          minTime,
          maxTime,
          queriesPerSecond: 1000 / avgTime
        })
      }

      metrics.database.queries = queryResults

      testLogger.performance('database-queries', queryResults.length, 'query-types', { results: queryResults })

      // Validate query performance
      for (const result of queryResults) {
        expect(result.avgTime).to.be.below(1000) // Average query time under 1 second
        expect(result.queriesPerSecond).to.be.above(10) // Minimum 10 queries per second
      }

      perfMonitor.endTimer('database-complex-queries')
    })
  })

  describe('System Resource Monitoring', function() {
    it('should monitor memory usage under load', async function() {
      perfMonitor.startTimer('memory-monitoring')

      const initialMemory = process.memoryUsage()
      const memorySnapshots = [initialMemory]

      // Generate load to test memory usage
      const loadPromises = []

      for (let i = 0; i < 1000; i++) {
        loadPromises.push(
          request('http://localhost:5678')
            .get('/api/characters')
            .timeout(5000)
        )

        // Take memory snapshot every 100 requests
        if (i % 100 === 0) {
          setTimeout(() => {
            memorySnapshots.push(process.memoryUsage())
          }, 0)
        }
      }

      await Promise.all(loadPromises)

      const finalMemory = process.memoryUsage()
      memorySnapshots.push(finalMemory)

      const memoryGrowth = {
        rss: finalMemory.rss - initialMemory.rss,
        heapUsed: finalMemory.heapUsed - initialMemory.heapUsed,
        heapTotal: finalMemory.heapTotal - initialMemory.heapTotal,
        external: finalMemory.external - initialMemory.external
      }

      metrics.system.memory = {
        initial: initialMemory,
        final: finalMemory,
        growth: memoryGrowth,
        snapshots: memorySnapshots
      }

      testLogger.performance('memory-growth', memoryGrowth.heapUsed / 1024 / 1024, 'MB', memoryGrowth)

      // Memory growth should be reasonable
      expect(memoryGrowth.heapUsed).to.be.below(100 * 1024 * 1024) // Less than 100MB growth

      perfMonitor.endTimer('memory-monitoring')
    })

    it('should monitor CPU usage under load', async function() {
      perfMonitor.startTimer('cpu-monitoring')

      const startCPU = process.cpuUsage()
      const cpuSnapshots = []

      // Generate CPU-intensive load
      const cpuIntensiveTasks = []

      for (let i = 0; i < 100; i++) {
        cpuIntensiveTasks.push(
          new Promise(resolve => {
            // Simulate CPU work
            const startTime = performance.now()
            let counter = 0
            while (performance.now() - startTime < 10) { // 10ms of work
              counter++
            }
            resolve(counter)
          })
        )
      }

      // Monitor CPU during tasks
      const monitorInterval = setInterval(() => {
        cpuSnapshots.push(process.cpuUsage(startCPU))
      }, 100)

      await Promise.all(cpuIntensiveTasks)
      clearInterval(monitorInterval)

      const endCPU = process.cpuUsage(startCPU)

      metrics.system.cpu = {
        start: startCPU,
        end: endCPU,
        snapshots: cpuSnapshots,
        user: endCPU.user,
        system: endCPU.system
      }

      testLogger.performance('cpu-usage', endCPU.user, 'microseconds', endCPU)

      perfMonitor.endTimer('cpu-monitoring')
    })
  })

  describe('Stress Testing and Limits', function() {
    it('should identify system breaking points', async function() {
      perfMonitor.startTimer('stress-testing')

      const maxConnections = 2000
      const batchSize = 100
      const stressResults = []

      for (let currentConnections = 0; currentConnections < maxConnections; currentConnections += batchSize) {
        const batchConnections = []
        const batchStartTime = performance.now()

        // Create batch of connections
        for (let i = 0; i < batchSize; i++) {
          const socket = io('http://localhost:5678', {
            transports: ['websocket'],
            forceNew: true,
            timeout: 5000
          })

          batchConnections.push(socket)
        }

        // Wait for connections to establish or timeout
        await new Promise(resolve => setTimeout(resolve, 5000))

        const connectedCount = batchConnections.filter(s => s.connected).length
        const batchEndTime = performance.now()
        const batchTime = batchEndTime - batchStartTime

        stressResults.push({
          totalConnections: currentConnections + batchSize,
          batchConnections: batchSize,
          connectedInBatch: connectedCount,
          batchConnectionTime: batchTime,
          batchSuccessRate: (connectedCount / batchSize) * 100
        })

        // Break early if success rate drops significantly
        if (connectedCount / batchSize < 0.8) {
          testLogger.warning(`Connection success rate dropped to ${(connectedCount / batchSize) * 100}% at ${currentConnections + batchSize} connections`)
          break
        }

        // Keep connections alive for this round
        connections.push(...batchConnections.filter(s => s.connected))

        // Brief pause between batches
        await new Promise(resolve => setTimeout(resolve, 2000))
      }

      metrics.system.stressTest = stressResults

      testLogger.performance('stress-test-max-connections', connections.length, 'connections', stressResults)

      // Find the maximum successful connections
      const successfulResults = stressResults.filter(r => r.batchSuccessRate > 80)
      const maxSuccessfulConnections = successfulResults.length > 0
        ? successfulResults[successfulResults.length - 1].totalConnections
        : 0

      expect(maxSuccessfulConnections).to.be.at.least(500) // Should handle at least 500 concurrent connections

      perfMonitor.endTimer('stress-testing')
    })

    it('should test graceful degradation under extreme load', async function() {
      perfMonitor.startTimer('graceful-degradation')

      const extremeLoad = 10000 // requests
      const promises = []
      const startTime = performance.now()

      // Generate extreme load
      for (let i = 0; i < extremeLoad; i++) {
        promises.push(
          request('http://localhost:5678')
            .get('/api/characters')
            .timeout(1000)
            .catch(err => ({ error: err.message, timeout: true }))
        )
      }

      const results = await Promise.allSettled(promises)
      const endTime = performance.now()

      const successful = results.filter(r =>
        r.status === 'fulfilled' &&
        !r.value.timeout &&
        r.value.statusCode === 200
      ).length

      const timeouts = results.filter(r =>
        r.status === 'fulfilled' &&
        r.value.timeout
      ).length

      const errors = results.filter(r => r.status === 'rejected').length

      const degradationMetrics = {
        totalRequests: extremeLoad,
        successful,
        timeouts,
        errors,
        totalTime: endTime - startTime,
        requestsPerSecond: (extremeLoad / (endTime - startTime)) * 1000,
        successRate: (successful / extremeLoad) * 100,
        timeoutRate: (timeouts / extremeLoad) * 100,
        errorRate: (errors / extremeLoad) * 100
      }

      metrics.system.degradation = degradationMetrics

      testLogger.performance('extreme-load', degradationMetrics.requestsPerSecond, 'req/s', degradationMetrics)

      // System should maintain some level of service even under extreme load
      expect(degradationMetrics.successRate).to.be.at.least(50) // At least 50% success rate
      expect(degradationMetrics.requestsPerSecond).to.be.at.least(100) // Minimum throughput maintained

      perfMonitor.endTimer('graceful-degradation')
    })
  })

  describe('Performance Report Generation', function() {
    it('should generate comprehensive performance report', async function() {
      perfMonitor.startTimer('report-generation')

      const performanceReport = {
        testSuite: 'load-testing',
        timestamp: new Date().toISOString(),
        duration: perfMonitor.getSummary().totalDuration,
        environment: config.environment,
        metrics: metrics,
        thresholds: {
          api: {
            minRequestsPerSecond: 100,
            maxAverageResponseTime: 1000,
            minSuccessRate: 95
          },
          websocket: {
            minConnections: 1000,
            maxLatency: 100,
            minMessageRate: 1000
          },
          database: {
            minOperationsPerSecond: 1000,
            maxQueryTime: 1000
          },
          system: {
            maxMemoryGrowth: 100 * 1024 * 1024, // 100MB
            maxConnections: 2000
          }
        },
        recommendations: []
      }

      // Generate recommendations based on metrics
      if (metrics.api.autocannon && metrics.api.autocannon.latency.average > 500) {
        performanceReport.recommendations.push('Consider implementing API response caching')
      }

      if (metrics.system.stressTest) {
        const maxConnections = metrics.system.stressTest[metrics.system.stressTest.length - 1]?.totalConnections || 0
        if (maxConnections < 1000) {
          performanceReport.recommendations.push('Consider optimizing WebSocket connection handling')
        }
      }

      if (metrics.system.memory && metrics.system.memory.growth.heapUsed > 50 * 1024 * 1024) {
        performanceReport.recommendations.push('Investigate potential memory leaks in long-running processes')
      }

      // Save report
      const reportPath = `${config.paths.reports}/load-testing-report-${Date.now()}.json`
      const fs = require('fs')
      fs.writeFileSync(reportPath, JSON.stringify(performanceReport, null, 2))

      testLogger.info(`Performance report generated: ${reportPath}`)

      expect(performanceReport.metrics).to.be.an('object')
      expect(performanceReport.recommendations).to.be.an('array')

      perfMonitor.endTimer('report-generation')
    })
  })
})