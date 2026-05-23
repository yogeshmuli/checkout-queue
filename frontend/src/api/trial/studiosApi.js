import { httpClient } from '../httpClient.js';
import { trialRequest } from './request.js';

export function listTrialStudios(params = {}) {
  return trialRequest(() => httpClient.get('/trial/studios', { params }));
}

export function createTrialStudio(payload) {
  return trialRequest(() => httpClient.post('/trial/studios', payload));
}

export function updateTrialStudio(studioId, payload) {
  return trialRequest(() => httpClient.patch(`/trial/studios/${studioId}`, payload));
}

export function deleteTrialStudio(studioId) {
  return trialRequest(() => httpClient.delete(`/trial/studios/${studioId}`));
}
