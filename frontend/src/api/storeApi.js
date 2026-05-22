import { httpClient, normalizeApiError } from './httpClient.js';

export async function listStores(params = {}) {
  try {
    const response = await httpClient.get('/stores', { params });
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function createStore(payload) {
  try {
    const response = await httpClient.post('/stores', payload);
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function updateStore(storeId, payload) {
  try {
    const response = await httpClient.patch(`/stores/${storeId}`, payload);
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function deleteStore(storeId) {
  try {
    const response = await httpClient.delete(`/stores/${storeId}`);
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

