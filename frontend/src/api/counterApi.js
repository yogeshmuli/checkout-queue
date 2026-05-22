import { httpClient, normalizeApiError } from './httpClient.js';

export async function listCounters(params = {}) {
  try {
    const response = await httpClient.get('/counters', { params });
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function createCounter(payload) {
  try {
    const response = await httpClient.post('/counters', payload);
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function updateCounter(counterId, payload) {
  try {
    const response = await httpClient.patch(`/counters/${counterId}`, payload);
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function deleteCounter(counterId) {
  try {
    const response = await httpClient.delete(`/counters/${counterId}`);
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}