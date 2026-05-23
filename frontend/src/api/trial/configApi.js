import { httpClient } from '../httpClient.js';
import { trialRequest } from './request.js';

export function getTrialConfig(storeId) {
  return trialRequest(() => httpClient.get(`/stores/${storeId}/trial-config`));
}

export function updateTrialConfig(storeId, payload) {
  return trialRequest(() => httpClient.put(`/stores/${storeId}/trial-config`, payload));
}
