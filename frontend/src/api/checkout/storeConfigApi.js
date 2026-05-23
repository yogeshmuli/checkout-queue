import { httpClient, normalizeApiError } from '../httpClient.js';

export async function getStoreConfig(storeId) {
  try {
    const response = await httpClient.get(`/stores/${storeId}/config`);
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function updateStoreConfig(storeId, payload) {
  try {
    const response = await httpClient.put(`/stores/${storeId}/config`, payload);
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}
