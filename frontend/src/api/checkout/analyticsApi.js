import { httpClient, normalizeApiError } from '../httpClient.js';

export async function getStoreAnalytics(storeId, params = {}) {
  try {
    const response = await httpClient.get(`/analytics/stores/${storeId}`, { params });
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}
