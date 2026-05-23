import { httpClient } from '../httpClient.js';
import { trialRequest } from './request.js';

export function listTrialStoreZones() {
  return trialRequest(() => httpClient.get('/trial/queue/store-zones'));
}

export function joinTrialQueue(payload) {
  return trialRequest(() => httpClient.post('/trial/queue/join', payload));
}

export function getTrialTokenStatus(params) {
  return trialRequest(() => httpClient.get('/trial/queue/status', { params }));
}

export function listTrialQueueTokens(params = {}) {
  return trialRequest(() => httpClient.get('/trial/queue/tokens', { params }));
}

export function startTrialToken(tokenId) {
  return trialRequest(() => httpClient.post(`/trial/queue/tokens/${tokenId}/start`));
}

export function completeTrialToken(tokenId) {
  return trialRequest(() => httpClient.post(`/trial/queue/tokens/${tokenId}/complete`));
}

export function cancelTrialToken(tokenId, cancellationReason) {
  return trialRequest(() =>
    httpClient.post(`/trial/queue/tokens/${tokenId}/cancel`, {
      cancellation_reason: cancellationReason || 'Cancelled from trial queue',
    })
  );
}
