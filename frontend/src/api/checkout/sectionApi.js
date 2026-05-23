import { httpClient, normalizeApiError } from '../httpClient.js';

export async function listSections(params = {}) {
  try {
    const response = await httpClient.get('/sections', { params });
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function createSection(payload) {
  try {
    const response = await httpClient.post('/sections', payload);
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function updateSection(sectionId, payload) {
  try {
    const response = await httpClient.patch(`/sections/${sectionId}`, payload);
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function deleteSection(sectionId) {
  try {
    const response = await httpClient.delete(`/sections/${sectionId}`);
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}
