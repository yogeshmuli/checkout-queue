import { httpClient } from '../httpClient.js';
import { trialRequest } from './request.js';

export function listTrialZones(params = {}) {
  return trialRequest(() => httpClient.get('/trial/zones', { params }));
}

export function createTrialZone(payload) {
  return trialRequest(() => httpClient.post('/trial/zones', payload));
}

export function updateTrialZone(zoneId, payload) {
  return trialRequest(() => httpClient.patch(`/trial/zones/${zoneId}`, payload));
}

export function deleteTrialZone(zoneId) {
  return trialRequest(() => httpClient.delete(`/trial/zones/${zoneId}`));
}
