import { httpClient } from './httpClient.js';

export function joinQueue(payload) {
  return httpClient.post('/queue/join', payload).then((response) => response.data);
}

export function getTokenStatus(params) {
  return httpClient.get('/queue/status', { params }).then((response) => response.data);
}

export function getCounterQueue(counterId) {
  return httpClient.get(`/queue/counters/${counterId}/tokens`).then((response) => response.data);
}

export function updateCounterStatus(counterId, payload) {
  return httpClient.patch(`/queue/counters/${counterId}/status`, payload).then((response) => response.data);
}

export function startToken(tokenId) {
  return httpClient.post(`/queue/tokens/${tokenId}/start`).then((response) => response.data);
}

export function completeToken(tokenId) {
  return httpClient.post(`/queue/tokens/${tokenId}/complete`).then((response) => response.data);
}

export function cancelToken(tokenId, cancellationReason) {
  return httpClient
    .post(`/queue/tokens/${tokenId}/cancel`, { cancellation_reason: cancellationReason || 'Cancelled from staff console' })
    .then((response) => response.data);
}
