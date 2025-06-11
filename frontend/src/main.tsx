import * as React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

// Add error handler for uncaught errors
window.addEventListener('error', (event) => {
  console.error('Global error:', event.error);
});

window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled promise rejection:', event.reason);
});

const rootElement = document.getElementById('root');
console.log('Root element:', rootElement);

if (!rootElement) {
  throw new Error('Failed to find the root element');
}

console.log('Creating root...');
const root = ReactDOM.createRoot(rootElement);

console.log('Rendering application...');
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
console.log('Application rendered'); 