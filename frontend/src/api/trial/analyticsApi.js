import { httpClient, normalizeApiError } from '../httpClient.js';

export async function getTrialStoreAnalytics(storeId, params = {}) {
  try {
    const response = await httpClient.get(`/trial/analytics/stores/${storeId}`, { params });
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}
