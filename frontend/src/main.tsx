import React from 'react';
import ReactDOM from 'react-dom/client';
import { ColorSchemeProvider } from 'gestalt';
import App from './App';
import './styles/global.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ColorSchemeProvider colorScheme="dark">
      <App />
    </ColorSchemeProvider>
  </React.StrictMode>
);
