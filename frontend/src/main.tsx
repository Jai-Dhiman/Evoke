import React from 'react';
import ReactDOM from 'react-dom/client';
import { ColorSchemeProvider } from 'gestalt';
import App from './App';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ColorSchemeProvider colorScheme="light">
      <App />
    </ColorSchemeProvider>
  </React.StrictMode>
);
