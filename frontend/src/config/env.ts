export const env = {
  API_URL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  APP_NAME: import.meta.env.VITE_APP_NAME || 'YUGI-AI',
  APP_VERSION: import.meta.env.VITE_APP_VERSION || '0.1.0',
};
