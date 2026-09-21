#!/usr/bin/env node

/**
 * Test Execution Script for DMlogn8n Integration Testing
 *
 * Command-line interface for running integration tests with various options:
 * - Select specific test suites to run
 * - Configure parallel execution and workers
 * - Enable/disable coverage and reports
 * - Integration with CI/CD pipelines
 * - Performance monitoring and reporting
 */

const path = require('path')
const { TestRunner } = require('../src/utils/TestRunner')
const { config } = require('../config/test-config')
const { testLogger } = require('../src/utils/logger')

// Parse command line arguments
const args = process.argv.slice(2)
const options = {
  suites: [],
  parallel: true,
  maxWorkers: require('os').cpus().length,
  coverage: true,
  reports: true,
  bail: false,
  timeout: 300000,
  retries: 2
}

// Parse arguments
for (let i = 0; i < args.length; i++) {
  const arg = args[i]

  switch (arg) {
    case '--suites':
    case '-s':
      options.suites = args[++i].split(',')
      break

    case '--parallel':
    case '-p':
      options.parallel = args[++i] !== 'false'
      break

    case '--workers':
    case '-w':
      options.maxWorkers = parseInt(args[++i])
      break

    case '--no-coverage':
      options.coverage = false
      break

    case '--no-reports':
      options.reports = false
      break

    case '--bail':
    case '-b':
      options.bail = true
      break

    case '--timeout':
    case '-t':
      options.timeout = parseInt(args[++i]) * 1000 // Convert to milliseconds
      break

    case '--retries':
    case '-r':
      options.retries = parseInt(args[++i])
      break

    case '--help':
    case '-h':
      showHelp()
      process.exit(0)

    case '--version':
    case '-v':
      console.log('DMlogn8n Integration Test Runner v1.0.0')
      process.exit(0)

    default:
      if (arg.startsWith('--')) {
        console.error(`Unknown option: ${arg}`)
        console.error('Use --help for available options')
        process.exit(1)
      }
  }
}

/**
 * Show help information
 */
function showHelp() {
  console.log(`
DMlogn8n Integration Test Runner

USAGE:
  node scripts/run-tests.js [OPTIONS]

OPTIONS:
  -s, --suites <list>        Comma-separated list of test suites to run
                              (integration, e2e, performance, scenarios)
  -p, --parallel <bool>      Enable parallel test execution (default: true)
  -w, --workers <number>     Maximum number of worker processes
  --no-coverage             Disable code coverage collection
  --no-reports              Disable report generation
  -b, --bail                Stop on first test failure
  -t, --timeout <seconds>   Test timeout in seconds (default: 300)
  -r, --retries <number>    Number of retries for failed tests
  -h, --help               Show this help message
  -v, --version            Show version information

EXAMPLES:
  node scripts/run-tests.js
  node scripts/run-tests.js --suites integration,e2e
  node scripts/run-tests.js --parallel false --bail
  node scripts/run-tests.js --no-coverage --timeout 600

ENVIRONMENT VARIABLES:
  NODE_ENV=test              Set Node environment
  TEST_ENV=development       Test environment type
  CI=true                   Enable CI mode
`)
}

/**
 * Main execution function
 */
async function main() {
  try {
    testLogger.info('Starting DMlogn8n Integration Test Runner')
    testLogger.info(`Options: ${JSON.stringify(options, null, 2)}`)

    // Validate options
    if (options.suites.length > 0) {
      const validSuites = ['integration', 'e2e', 'performance', 'scenarios']
      const invalidSuites = options.suites.filter(s => !validSuites.includes(s))

      if (invalidSuites.length > 0) {
        throw new Error(`Invalid test suites: ${invalidSuites.join(', ')}`)
      }
    }

    // Create and configure test runner
    const testRunner = new TestRunner(options)

    // Set up event listeners
    testRunner.on('run-start', () => {
      testLogger.info('Test execution started')
    })

    testRunner.on('run-complete', ({ success, results }) => {
      if (success) {
        testLogger.info('All tests passed successfully! ✅')
      } else {
        testLogger.error('Some tests failed! ❌')
      }

      // Print summary
      console.log('\n=== Test Summary ===')
      console.log(`Total suites: ${results.length}`)
      console.log(`Passed: ${results.filter(r => r.success).length}`)
      console.log(`Failed: ${results.filter(r => !r.success).length}`)
      console.log(`Duration: ${Date.now() - testRunner.getState().startTime}ms`)

      // Print suite details
      for (const result of results) {
        const status = result.success ? '✅' : '❌'
        console.log(`${status} ${result.suite} (${result.duration}ms) - ${result.tests?.length || 0} tests`)
      }
    })

    testRunner.on('run-error', (error) => {
      testLogger.error(`Test execution failed: ${error.message}`)
    })

    testRunner.on('suite-start', (suite) => {
      testLogger.info(`Running suite: ${suite.name}`)
    })

    testRunner.on('suite-complete', ({ suite, result }) => {
      const status = result.success ? '✅' : '❌'
      testLogger.info(`${status} ${suite.name} completed in ${result.duration}ms`)
    })

    testRunner.on('suite-error', ({ suite, error }) => {
      testLogger.error(`❌ ${suite.name} failed: ${error.message}`)
    })

    testRunner.on('environment-setup-start', () => {
      testLogger.info('Setting up test environment...')
    })

    testRunner.on('environment-setup-complete', () => {
      testLogger.info('Test environment ready')
    })

    testRunner.on('environment-setup-error', (error) => {
      testLogger.error(`Environment setup failed: ${error.message}`)
    })

    testRunner.on('reports-generation-start', () => {
      testLogger.info('Generating test reports...')
    })

    testRunner.on('reports-generation-complete', () => {
      testLogger.info('Test reports generated')
    })

    testRunner.on('reports-generation-error', (error) => {
      testLogger.error(`Report generation failed: ${error.message}`)
    })

    // Run tests
    const { success, results } = await testRunner.run()

    // Exit with appropriate code
    process.exit(success ? 0 : 1)

  } catch (error) {
    testLogger.error(`Test runner failed: ${error.message}`)
    console.error(error.stack)
    process.exit(1)
  }
}

// Handle unhandled promise rejections
process.on('unhandledRejection', (reason, promise) => {
  testLogger.error('Unhandled Rejection at:', promise, 'reason:', reason)
  process.exit(1)
})

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  testLogger.error('Uncaught Exception:', error)
  process.exit(1)
})

// Handle termination signals
process.on('SIGINT', () => {
  testLogger.info('Test execution interrupted by user')
  process.exit(130) // 128 + SIGINT
})

process.on('SIGTERM', () => {
  testLogger.info('Test execution terminated')
  process.exit(143) // 128 + SIGTERM
})

// Run main function
if (require.main === module) {
  main()
}

module.exports = { main, options }