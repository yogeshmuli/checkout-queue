import { httpClient } from './httpClient.js';

export function loginUser(payload) {
  return httpClient.post('/auth/login', payload).then((response) => response.data);
}

export function registerUser(payload) {
  return httpClient.post('/auth/register', payload).then((response) => response.data);
}

export function fetchCurrentUser() {
  return httpClient.get('/auth/me').then((response) => response.data);
}

