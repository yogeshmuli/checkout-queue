import { httpClient } from '../httpClient.js';
import { trialRequest } from './request.js';

export function trainTrialStoreModel(storeId) {
  return trialRequest(() => httpClient.post(`/ml/trial/stores/${storeId}/train`));
}

export function getTrialStoreModelMetadata(storeId) {
  return trialRequest(() => httpClient.get(`/ml/trial/stores/${storeId}/metadata`));
}

export function downloadTrialStoreTrainingTemplate(storeId) {
  return trialRequest(() => httpClient.get(`/ml/trial/stores/${storeId}/training-template`, { responseType: 'blob' }));
}

export function trainTrialStoreModelFromUpload(storeId, file) {
  const formData = new FormData();
  formData.append('file', file);
  return trialRequest(() => httpClient.post(`/ml/trial/stores/${storeId}/train-upload`, formData));
}
