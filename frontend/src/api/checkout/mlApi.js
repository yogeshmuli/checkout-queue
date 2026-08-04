import { httpClient, normalizeApiError } from '../httpClient.js';

export async function trainStoreModel(storeId) {
  try {
    const response = await httpClient.post(`/ml/stores/${storeId}/train`);
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function getStoreModelMetadata(storeId) {
  try {
    const response = await httpClient.get(`/ml/stores/${storeId}/metadata`);
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function downloadStoreTrainingTemplate(storeId) {
  try {
    const response = await httpClient.get(`/ml/stores/${storeId}/training-template`, { responseType: 'blob' });
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function trainStoreModelFromUpload(storeId, file) {
  try {
    const formData = new FormData();
    formData.append('file', file);
    const response = await httpClient.post(`/ml/stores/${storeId}/train-upload`, formData);
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}
