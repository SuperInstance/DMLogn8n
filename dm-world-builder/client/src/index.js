import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

// Import CSS for additional styling
import './index.css';

// Import service worker
import * as serviceWorkerRegistration from './serviceWorkerRegistration';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// Register service worker
serviceWorkerRegistration.register();