import { httpClient } from '../httpClient.js';
import { trialRequest } from './request.js';

export function trainTrialStoreModel(storeId) {
  return trialRequest(() => httpClient.post(`/ml/trial/stores/${storeId}/train`));
}

export function getTrialStoreModelMetadata(storeId) {
  return trialRequest(() => httpClient.get(`/ml/trial/stores/${storeId}/metadata`));
}
