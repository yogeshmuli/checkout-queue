import { httpClient, normalizeApiError } from './httpClient.js';

export async function listStaff(params = {}) {
  try {
    const response = await httpClient.get('/staff', { params });
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function createStaff(payload) {
  try {
    const response = await httpClient.post('/staff', payload);
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function updateStaff(staffId, payload) {
  try {
    const response = await httpClient.patch(`/staff/${staffId}`, payload);
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function deleteStaff(staffId) {
  try {
    const response = await httpClient.delete(`/staff/${staffId}`);
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}
