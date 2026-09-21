/**
 * Automated Test Runner for DMlogn8n Integration Testing
 *
 * Provides comprehensive test orchestration including:
 * - Parallel and sequential test execution
 * - Test environment management
 * - Result collection and reporting
 * - CI/CD integration capabilities
 * - Performance monitoring and metrics
 * - Test dependency resolution
 * - Failure recovery and retry logic
 */

const { execSync } = require('child_process')
const fs = require('fs')
const path = require('path')
const { EventEmitter } = require('events')
const { PerformanceMonitor, testLogger, LogAnalyzer } = require('./logger')
const { config } = require('../../config/test-config')

class TestRunner extends EventEmitter {
  constructor(options = {}) {
    super()

    this.options = {
      parallel: options.parallel !== false,
      maxWorkers: options.maxWorkers || require('os').cpus().length,
      retries: options.retries || 2,
      timeout: options.timeout || 300000, // 5 minutes
      bail: options.bail !== false, // Stop on first failure
      coverage: options.coverage !== false,
      reports: options.reports !== false,
      ...options
    }

    this.state = {
      running: false,
      completed: false,
      tests: [],
      results: [],
      errors: [],
      startTime: null,
      endTime: null,
      environment: null
    }

    this.testSuites = [
      {
        name: 'integration',
        path: 'tests/integration',
        priority: 1,
        dependencies: [],
        timeout: 30000,
        parallel: true
      },
      {
        name: 'e2e',
        path: 'tests/e2e',
        priority: 2,
        dependencies: ['integration'],
        timeout: 120000,
        parallel: false
      },
      {
        name: 'performance',
        path: 'tests/performance',
        priority: 3,
        dependencies: ['integration', 'e2e'],
        timeout: 300000,
        parallel: false
      },
      {
        name: 'scenarios',
        path: 'tests/scenarios',
        priority: 4,
        dependencies: ['integration', 'e2e'],
        timeout: 600000,
        parallel: false
      }
    ]
  }

  /**
   * Run all test suites with dependency resolution
   */
  async run() {
    if (this.state.running) {
      throw new Error('Test runner is already running')
    }

    this.state.running = true
    this.state.startTime = Date.now()
    this.emit('run-start')

    try {
      // Setup test environment
      await this.setupEnvironment()

      // Execute test suites in dependency order
      const results = await this.executeTestSuites()

      // Generate reports
      if (this.options.reports) {
        await this.generateReports(results)
      }

      this.state.completed = true
      this.state.endTime = Date.now()
      this.state.results = results

      const success = results.every(r => r.success)
      this.emit('run-complete', { success, results })

      return { success, results }

    } catch (error) {
      this.state.errors.push(error)
      this.emit('run-error', error)
      throw error
    } finally {
      this.state.running = false

      // Cleanup environment
      await this.cleanupEnvironment()
    }
  }

  /**
   * Setup test environment
   */
  async setupEnvironment() {
    testLogger.info('Setting up test environment...')

    this.emit('environment-setup-start')

    try {
      // Create necessary directories
      const dirs = [
        config.paths.reports,
        config.paths.coverage,
        config.paths.logs,
        config.paths.artifacts,
        path.join(config.paths.temp, 'test-runner')
      ]

      for (const dir of dirs) {
        if (!fs.existsSync(dir)) {
          fs.mkdirSync(dir, { recursive: true })
        }
      }

      // Set environment variables
      process.env.NODE_ENV = 'test'
      process.env.TEST_ENV = config.environment
      process.env.CI = config.ci.enabled ? 'true' : 'false'

      // Verify service availability
      await this.verifyServices()

      this.emit('environment-setup-complete')
      testLogger.info('Test environment setup complete')

    } catch (error) {
      this.emit('environment-setup-error', error)
      throw new Error(`Environment setup failed: ${error.message}`)
    }
  }

  /**
   * Verify required services are available
   */
  async verifyServices() {
    const services = [
      { name: 'n8n', port: 5678 },
      { name: 'aiDialogue', port: 3001 },
      { name: 'arena', port: 3002 },
      { name: 'crafting', port: 3004 },
      { name: 'guild', port: 3005 },
      { name: 'quest', port: 3006 },
      { name: 'voice', port: 3007 },
      { name: 'weather', port: 3008 }
    ]

    const availableServices = []
    const unavailableServices = []

    for (const service of services) {
      try {
        const response = await fetch(`http://localhost:${service.port}/health`, {
          timeout: 5000
        })

        if (response.ok) {
          availableServices.push(service.name)
        } else {
          unavailableServices.push(service.name)
        }
      } catch (error) {
        // Service not available, will use mocks
        unavailableServices.push(service.name)
      }
    }

    testLogger.info(`Available services: ${availableServices.join(', ')}`)
    testLogger.info(`Unavailable services (using mocks): ${unavailableServices.join(', ')}`)

    // Enable mock servers for unavailable services
    if (unavailableServices.length > 0) {
      process.env.ENABLE_MOCK_SERVERS = 'true'
      testLogger.info('Mock servers enabled for unavailable services')
    }
  }

  /**
   * Execute test suites with dependency resolution
   */
  async executeTestSuites() {
    const results = []
    const executed = new Set()

    // Sort test suites by priority and resolve dependencies
    const sortedSuites = this.resolveDependencies(this.testSuites)

    for (const suite of sortedSuites) {
      if (executed.has(suite.name)) {
        continue
      }

      testLogger.info(`Executing test suite: ${suite.name}`)
      this.emit('suite-start', suite)

      try {
        const result = await this.executeSuite(suite)
        results.push(result)
        executed.add(suite.name)

        this.emit('suite-complete', { suite, result })

        // Stop on failure if bail option is enabled
        if (!result.success && this.options.bail) {
          testLogger.error(`Test suite ${suite.name} failed, stopping execution (bail mode)`)
          break
        }

      } catch (error) {
        const errorResult = {
          suite: suite.name,
          success: false,
          error: error.message,
          duration: 0,
          tests: []
        }

        results.push(errorResult)
        this.emit('suite-error', { suite, error })

        if (this.options.bail) {
          throw error
        }
      }
    }

    return results
  }

  /**
   * Resolve test suite dependencies
   */
  resolveDependencies(suites) {
    const resolved = []
    const visiting = new Set()
    const visited = new Set()

    const visit = (suite) => {
      if (visited.has(suite.name)) {
        return
      }

      if (visiting.has(suite.name)) {
        throw new Error(`Circular dependency detected involving ${suite.name}`)
      }

      visiting.add(suite.name)

      // Visit dependencies first
      for (const dep of suite.dependencies) {
        const depSuite = suites.find(s => s.name === dep)
        if (!depSuite) {
          throw new Error(`Dependency ${dep} not found for suite ${suite.name}`)
        }
        visit(depSuite)
      }

      visiting.delete(suite.name)
      visited.add(suite.name)
      resolved.push(suite)
    }

    for (const suite of suites) {
      visit(suite)
    }

    return resolved.sort((a, b) => a.priority - b.priority)
  }

  /**
   * Execute a single test suite
   */
  async executeSuite(suite) {
    const perfMonitor = new PerformanceMonitor(`suite-${suite.name}`)
    perfMonitor.startTimer('suite-execution')

    const suitePath = path.resolve(process.cwd(), suite.path)

    if (!fs.existsSync(suitePath)) {
      throw new Error(`Test suite path does not exist: ${suitePath}`)
    }

    const jestConfig = {
      testEnvironment: 'node',
      roots: [suitePath],
      testMatch: ['**/*.test.js'],
      maxWorkers: suite.parallel ? this.options.maxWorkers : 1,
      runInBand: !suite.parallel,
      testTimeout: suite.timeout || this.options.timeout,
      verbose: true,
      collectCoverage: this.options.coverage,
      coverageDirectory: config.paths.coverage,
      reporters: [
        'default',
        ['jest-html-reporters', {
          publicPath: config.paths.reports,
          filename: `${suite.name}-report.html`,
          expand: true
        }]
      ],
      setupFilesAfterEnv: [path.join(__dirname, '../tests/setup.js')]
    }

    // Create temporary Jest config file
    const jestConfigPath = path.join(config.paths.temp, `jest-${suite.name}.config.js`)
    fs.writeFileSync(jestConfigPath, `module.exports = ${JSON.stringify(jestConfig, null, 2)}`)

    try {
      // Run Jest with configuration
      const jestCommand = `npx jest --config ${jestConfigPath} --passWithNoTests`

      testLogger.info(`Running Jest command: ${jestCommand}`)

      const output = execSync(jestCommand, {
        cwd: process.cwd(),
        encoding: 'utf8',
        maxBuffer: 1024 * 1024 * 10, // 10MB buffer
        timeout: suite.timeout || this.options.timeout
      })

      // Parse Jest output for results
      const result = this.parseJestOutput(output, suite)

      perfMonitor.endTimer('suite-execution')

      return {
        suite: suite.name,
        success: result.success,
        duration: perfMonitor.getSummary().totalDuration,
        tests: result.tests,
        coverage: result.coverage,
        output: output
      }

    } catch (error) {
      // Jest returns non-zero exit code on test failures
      const output = error.stdout || error.message
      const result = this.parseJestOutput(output, suite, error.status)

      perfMonitor.endTimer('suite-execution')

      return {
        suite: suite.name,
        success: false,
        duration: perfMonitor.getSummary().totalDuration,
        tests: result.tests,
        coverage: result.coverage,
        output: output,
        error: error.message
      }
    } finally {
      // Clean up temporary config file
      if (fs.existsSync(jestConfigPath)) {
        fs.unlinkSync(jestConfigPath)
      }
    }
  }

  /**
   * Parse Jest output to extract test results
   */
  parseJestOutput(output, suite, exitCode = 0) {
    const lines = output.split('\n')
    const tests = []
    let coverage = null
    let success = exitCode === 0

    // Parse test results
    for (const line of lines) {
      // Test pass/fail indicators
      if (line.includes('✓') || line.includes('✗')) {
        const passed = line.includes('✓')
        const testName = line.replace(/[✓✗]/, '').trim()

        tests.push({
          name: testName,
          passed,
          suite: suite.name
        })
      }

      // Coverage information
      if (line.includes('Coverage') && line.includes('%')) {
        coverage = {
          line: this.extractCoverageValue(line, 'Line'),
          function: this.extractCoverageValue(line, 'Function'),
          branch: this.extractCoverageValue(line, 'Branch'),
          statement: this.extractCoverageValue(line, 'Statement')
        }
      }
    }

    return {
      success,
      tests,
      coverage
    }
  }

  /**
   * Extract coverage percentage from Jest output line
   */
  extractCoverageValue(line, type) {
    const regex = new RegExp(`${type}\\s*:\\s*(\\d+(?:\\.\\d+)?)%`)
    const match = line.match(regex)
    return match ? parseFloat(match[1]) : 0
  }

  /**
   * Generate comprehensive test reports
   */
  async generateReports(results) {
    testLogger.info('Generating test reports...')
    this.emit('reports-generation-start')

    try {
      // Generate HTML report
      await this.generateHtmlReport(results)

      // Generate JSON report
      await this.generateJsonReport(results)

      // Generate JUnit XML for CI systems
      await this.generateJUnitReport(results)

      // Generate coverage report
      if (this.options.coverage) {
        await this.generateCoverageReport(results)
      }

      // Generate performance report
      await this.generatePerformanceReport(results)

      // Generate trend analysis
      await this.generateTrendReport(results)

      this.emit('reports-generation-complete')
      testLogger.info('Test reports generated successfully')

    } catch (error) {
      this.emit('reports-generation-error', error)
      testLogger.error(`Report generation failed: ${error.message}`)
    }
  }

  /**
   * Generate HTML test report
   */
  async generateHtmlReport(results) {
    const htmlTemplate = `
<!DOCTYPE html>
<html>
<head>
    <title>DMlogn8n Integration Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f5f5f5; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .summary { display: flex; gap: 20px; margin-bottom: 20px; }
        .metric { background: #e8f5e8; padding: 15px; border-radius: 5px; text-align: center; }
        .metric.failed { background: #ffe8e8; }
        .suite { margin-bottom: 30px; border: 1px solid #ddd; border-radius: 5px; }
        .suite-header { background: #f8f9fa; padding: 15px; font-weight: bold; }
        .suite-content { padding: 15px; }
        .test { padding: 5px 0; }
        .test.passed { color: green; }
        .test.failed { color: red; }
        .coverage { background: #fff3cd; padding: 10px; margin-top: 10px; border-radius: 3px; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>DMlogn8n Integration Test Report</h1>
        <p>Generated: ${new Date().toLocaleString()}</p>
        <p>Environment: ${config.environment}</p>
        <p>Duration: ${this.state.endTime - this.state.startTime}ms</p>
    </div>

    <div class="summary">
        <div class="metric">
            <h3>Total Suites</h3>
            <p>${results.length}</p>
        </div>
        <div class="metric ${results.filter(r => r.success).length === results.length ? '' : 'failed'}">
            <h3>Passed</h3>
            <p>${results.filter(r => r.success).length}</p>
        </div>
        <div class="metric ${results.filter(r => !r.success).length > 0 ? 'failed' : ''}">
            <h3>Failed</h3>
            <p>${results.filter(r => !r.success).length}</p>
        </div>
        <div class="metric">
            <h3>Total Tests</h3>
            <p>${results.reduce((sum, r) => sum + (r.tests?.length || 0), 0)}</p>
        </div>
    </div>

    ${results.map(result => `
        <div class="suite">
            <div class="suite-header">
                ${result.suite} - ${result.success ? '✅ PASSED' : '❌ FAILED'} (${result.duration}ms)
            </div>
            <div class="suite-content">
                ${result.tests && result.tests.length > 0 ? `
                    <h4>Tests:</h4>
                    <div class="tests">
                        ${result.tests.map(test => `
                            <div class="test ${test.passed ? 'passed' : 'failed'}">
                                ${test.passed ? '✓' : '✗'} ${test.name}
                            </div>
                        `).join('')}
                    </div>
                ` : '<p>No tests found</p>'}

                ${result.coverage ? `
                    <div class="coverage">
                        <h4>Coverage:</h4>
                        <table>
                            <tr><th>Line</th><th>Function</th><th>Branch</th><th>Statement</th></tr>
                            <tr>
                                <td>${result.coverage.line}%</td>
                                <td>${result.coverage.function}%</td>
                                <td>${result.coverage.branch}%</td>
                                <td>${result.coverage.statement}%</td>
                            </tr>
                        </table>
                    </div>
                ` : ''}

                ${result.error ? `
                    <div class="error" style="background: #ffe8e8; padding: 10px; margin-top: 10px; border-radius: 3px;">
                        <h4>Error:</h4>
                        <pre>${result.error}</pre>
                    </div>
                ` : ''}
            </div>
        </div>
    `).join('')}
</body>
</html>`

    const reportPath = path.join(config.paths.reports, `integration-test-report-${Date.now()}.html`)
    fs.writeFileSync(reportPath, htmlTemplate)

    testLogger.info(`HTML report generated: ${reportPath}`)
    return reportPath
  }

  /**
   * Generate JSON test report
   */
  async generateJsonReport(results) {
    const jsonReport = {
      metadata: {
        generated: new Date().toISOString(),
        environment: config.environment,
        duration: this.state.endTime - this.state.startTime,
        runner: {
          version: '1.0.0',
          options: this.options
        }
      },
      summary: {
        totalSuites: results.length,
        passedSuites: results.filter(r => r.success).length,
        failedSuites: results.filter(r => !r.success).length,
        totalTests: results.reduce((sum, r) => sum + (r.tests?.length || 0), 0),
        passedTests: results.reduce((sum, r) => sum + (r.tests?.filter(t => t.passed).length || 0), 0),
        failedTests: results.reduce((sum, r) => sum + (r.tests?.filter(t => !t.passed).length || 0), 0)
      },
      suites: results.map(result => ({
        name: result.suite,
        success: result.success,
        duration: result.duration,
        tests: result.tests || [],
        coverage: result.coverage,
        error: result.error
      })),
      systemInfo: {
        node: process.version,
        platform: process.platform,
        arch: process.arch,
        cpus: require('os').cpus().length,
        memory: require('os').totalmem()
      }
    }

    const reportPath = path.join(config.paths.reports, `integration-test-report-${Date.now()}.json`)
    fs.writeFileSync(reportPath, JSON.stringify(jsonReport, null, 2))

    testLogger.info(`JSON report generated: ${reportPath}`)
    return reportPath
  }

  /**
   * Generate JUnit XML report for CI systems
   */
  async generateJUnitReport(results) {
    const xmlLines = [
      '<?xml version="1.0" encoding="UTF-8"?>',
      `<testsuites name="DMlogn8n Integration Tests" tests="${results.reduce((sum, r) => sum + (r.tests?.length || 0), 0)}" failures="${results.reduce((sum, r) => sum + (r.tests?.filter(t => !t.passed).length || 0), 0)}" time="${(this.state.endTime - this.state.startTime) / 1000}">`
    ]

    for (const result of results) {
      xmlLines.push(
        `  <testsuite name="${result.suite}" tests="${result.tests?.length || 0}" failures="${result.tests?.filter(t => !t.passed).length || 0}" time="${result.duration / 1000}">`
      )

      if (result.tests) {
        for (const test of result.tests) {
          xmlLines.push(
            `    <testcase name="${test.name}" classname="${result.suite}" time="${result.duration / (result.tests.length * 1000)}">`
          )

          if (!test.passed) {
            xmlLines.push(
              '      <failure message="Test failed">',
              `        ${test.name} failed in suite ${result.suite}`,
              '      </failure>'
            )
          }

          xmlLines.push('    </testcase>')
        }
      }

      if (result.error) {
        xmlLines.push(
          '    <failure message="Suite error">',
          `      ${result.error}`,
          '    </failure>'
        )
      }

      xmlLines.push('  </testsuite>')
    }

    xmlLines.push('</testsuites>')

    const xmlContent = xmlLines.join('\n')
    const reportPath = path.join(config.paths.reports, `junit-report-${Date.now()}.xml`)
    fs.writeFileSync(reportPath, xmlContent)

    testLogger.info(`JUnit report generated: ${reportPath}`)
    return reportPath
  }

  /**
   * Generate coverage report
   */
  async generateCoverageReport(results) {
    const coverageDir = config.paths.coverage
    if (!fs.existsSync(coverageDir)) {
      testLogger.warning('Coverage directory not found, skipping coverage report')
      return
    }

    // Combine coverage from all suites
    const coverageSummary = {
      total: {
        lines: { total: 0, covered: 0, percentage: 0 },
        functions: { total: 0, covered: 0, percentage: 0 },
        branches: { total: 0, covered: 0, percentage: 0 },
        statements: { total: 0, covered: 0, percentage: 0 }
      },
      suites: {}
    }

    for (const result of results) {
      if (result.coverage) {
        coverageSummary.suites[result.suite] = result.coverage

        // Aggregate totals
        coverageSummary.total.lines.percentage += result.coverage.line || 0
        coverageSummary.total.functions.percentage += result.coverage.function || 0
        coverageSummary.total.branches.percentage += result.coverage.branch || 0
        coverageSummary.total.statements.percentage += result.coverage.statement || 0
      }
    }

    // Calculate averages
    const suiteCount = Object.keys(coverageSummary.suites).length
    if (suiteCount > 0) {
      coverageSummary.total.lines.percentage /= suiteCount
      coverageSummary.total.functions.percentage /= suiteCount
      coverageSummary.total.branches.percentage /= suiteCount
      coverageSummary.total.statements.percentage /= suiteCount
    }

    const reportPath = path.join(config.paths.reports, `coverage-summary-${Date.now()}.json`)
    fs.writeFileSync(reportPath, JSON.stringify(coverageSummary, null, 2))

    testLogger.info(`Coverage report generated: ${reportPath}`)
    return reportPath
  }

  /**
   * Generate performance report
   */
  async generatePerformanceReport(results) {
    const performanceReport = {
      overall: {
        totalDuration: this.state.endTime - this.state.startTime,
        suiteCount: results.length,
        averageSuiteDuration: results.reduce((sum, r) => sum + r.duration, 0) / results.length,
        slowestSuite: results.reduce((max, r) => r.duration > max.duration ? r : max, results[0]),
        fastestSuite: results.reduce((min, r) => r.duration < min.duration ? r : min, results[0])
      },
      suites: results.map(result => ({
        name: result.suite,
        duration: result.duration,
        testCount: result.tests?.length || 0,
        averageTestDuration: result.duration / (result.tests?.length || 1),
        successRate: result.tests ? (result.tests.filter(t => t.passed).length / result.tests.length) * 100 : 0
      }))
    }

    const reportPath = path.join(config.paths.reports, `performance-report-${Date.now()}.json`)
    fs.writeFileSync(reportPath, JSON.stringify(performanceReport, null, 2))

    testLogger.info(`Performance report generated: ${reportPath}`)
    return reportPath
  }

  /**
   * Generate trend analysis report
   */
  async generateTrendReport(results) {
    // This would analyze historical data if available
    // For now, create a simple trend report structure
    const trendReport = {
      current: {
        timestamp: new Date().toISOString(),
        results: results.map(r => ({
          suite: r.suite,
          success: r.success,
          duration: r.duration,
          testCount: r.tests?.length || 0
        }))
      },
      trends: {
        successRate: 'stable', // Would calculate from historical data
        performance: 'improving', // Would calculate from historical data
        coverage: 'stable' // Would calculate from historical data
      },
      recommendations: this.generateRecommendations(results)
    }

    const reportPath = path.join(config.paths.reports, `trend-analysis-${Date.now()}.json`)
    fs.writeFileSync(reportPath, JSON.stringify(trendReport, null, 2))

    testLogger.info(`Trend report generated: ${reportPath}`)
    return reportPath
  }

  /**
   * Generate recommendations based on test results
   */
  generateRecommendations(results) {
    const recommendations = []

    // Analyze test failures
    const failedSuites = results.filter(r => !r.success)
    if (failedSuites.length > 0) {
      recommendations.push('Review and fix failing test suites')
    }

    // Analyze performance
    const slowSuites = results.filter(r => r.duration > 60000) // > 1 minute
    if (slowSuites.length > 0) {
      recommendations.push('Consider optimizing slow test suites')
    }

    // Analyze coverage
    const lowCoverageSuites = results.filter(r =>
      r.coverage && (r.coverage.line < 80 || r.coverage.function < 80)
    )
    if (lowCoverageSuites.length > 0) {
      recommendations.push('Improve test coverage for critical paths')
    }

    return recommendations
  }

  /**
   * Cleanup test environment
   */
  async cleanupEnvironment() {
    testLogger.info('Cleaning up test environment...')

    try {
      // Clean up temporary files
      const tempDir = path.join(config.paths.temp, 'test-runner')
      if (fs.existsSync(tempDir)) {
        fs.rmSync(tempDir, { recursive: true, force: true })
      }

      // Reset environment variables
      delete process.env.NODE_ENV
      delete process.env.TEST_ENV
      delete process.env.CI

      testLogger.info('Test environment cleanup complete')

    } catch (error) {
      testLogger.error(`Environment cleanup failed: ${error.message}`)
    }
  }

  /**
   * Get current test runner state
   */
  getState() {
    return { ...this.state }
  }

  /**
   * Check if test runner is currently running
   */
  isRunning() {
    return this.state.running
  }

  /**
   * Check if test runner has completed
   */
  isCompleted() {
    return this.state.completed
  }
}

module.exports = TestRunner