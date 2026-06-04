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

export function getTrialStudioQueue(studioId) {
  return trialRequest(() => httpClient.get(`/trial/queue/studios/${studioId}/tokens`));
}

export function getTrialZoneStudios(zoneId) {
  return trialRequest(() => httpClient.get(`/trial/queue/zones/${zoneId}/studios`));
}

export function updateTrialStudioStatus(studioId, payload) {
  return trialRequest(() => httpClient.patch(`/trial/queue/studios/${studioId}/status`, payload));
}

export function startTrialToken(tokenId) {
  return trialRequest(() => httpClient.post(`/trial/queue/tokens/${tokenId}/start`));
}

export function callTrialToken(tokenId) {
  return trialRequest(() =>
    httpClient.post('/trial/queue/events', {
      token_id: tokenId,
      event: 'CALLED',
    })
  );
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

export function cancelTrialCustomerToken(tokenId) {
  return trialRequest(() => httpClient.post(`/trial/queue/tokens/${tokenId}/customer-cancel`));
}

export function moveTrialCustomerTokenLast(tokenId) {
  return trialRequest(() => httpClient.post(`/trial/queue/tokens/${tokenId}/customer-move-last`));
}
