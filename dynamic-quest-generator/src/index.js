import { startServer } from './api/index.js'

// Start the Dynamic Quest Generator server
startServer().catch(error => {
  console.error('Failed to start Dynamic Quest Generator:', error)
  process.exit(1)
})