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
