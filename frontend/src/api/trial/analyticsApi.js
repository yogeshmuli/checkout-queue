import { httpClient, normalizeApiError } from '../httpClient.js';

export async function getTrialStoreAnalytics(storeId, params = {}, requestConfig = {}) {
  try {
    const response = await httpClient.get(`/trial/analytics/stores/${storeId}`, { ...requestConfig, params });
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}
