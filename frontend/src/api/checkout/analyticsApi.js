import { httpClient, normalizeApiError } from '../httpClient.js';

export async function getStoreAnalytics(storeId, params = {}, requestConfig = {}) {
  try {
    const response = await httpClient.get(`/analytics/stores/${storeId}`, { ...requestConfig, params });
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}
