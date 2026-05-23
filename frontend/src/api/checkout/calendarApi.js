import { httpClient, normalizeApiError } from '../httpClient.js';

export async function getStoreCalendar(storeId) {
  try {
    const response = await httpClient.get(`/stores/${storeId}/calendar`);
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function updateStoreCalendar(storeId, payload) {
  try {
    const response = await httpClient.put(`/stores/${storeId}/calendar`, payload);
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}
