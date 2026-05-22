import { httpClient, normalizeApiError } from './httpClient.js';

export async function loginUser(payload) {
  try {
    const response = await httpClient.post('/auth/login', payload);
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function registerUser(payload) {
  try {
    const response = await httpClient.post('/auth/register', payload);
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function fetchCurrentUser() {
  try {
    const response = await httpClient.get('/auth/me');
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

