import { httpClient, normalizeApiError } from './httpClient.js';

export async function getNotificationConfig(storeId) {
  try {
    const response = await httpClient.get(`/stores/${storeId}/notification-config`);
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function updateNotificationConfig(storeId, payload) {
  try {
    const response = await httpClient.put(`/stores/${storeId}/notification-config`, payload);
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function listNotificationLogs(storeId, params = {}) {
  try {
    const response = await httpClient.get(`/stores/${storeId}/notification-logs`, { params });
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}
