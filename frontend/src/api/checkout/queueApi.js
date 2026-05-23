import { httpClient, normalizeApiError } from '../httpClient.js';

export async function joinQueue(payload) {
  try {
    const response = await httpClient.post('/queue/join', payload);
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function getTokenStatus(params) {
  try {
    const response = await httpClient.get('/queue/status', { params });
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function listStoreSections() {
  try {
    const response = await httpClient.get('/queue/store-sections');
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function listQueueTokens(params = {}) {
  try {
    const response = await httpClient.get('/queue/tokens', { params });
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function getCounterQueue(counterId) {
  try {
    const response = await httpClient.get(`/queue/counters/${counterId}/tokens`);
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function updateCounterStatus(counterId, payload) {
  try {
    const response = await httpClient.patch(`/queue/counters/${counterId}/status`, payload);
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function callToken(tokenId) {
  try {
    const response = await httpClient.post('/queue/events', {
      token_id: tokenId,
      event: 'CALLED',
    });
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function startToken(tokenId) {
  try {
    const response = await httpClient.post(`/queue/tokens/${tokenId}/start`);
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function completeToken(tokenId) {
  try {
    const response = await httpClient.post(`/queue/tokens/${tokenId}/complete`);
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function cancelToken(tokenId, cancellationReason) {
  try {
    const response = await httpClient.post(`/queue/tokens/${tokenId}/cancel`, {
      cancellation_reason: cancellationReason || 'Cancelled from staff console',
    });
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function cancelCustomerToken(tokenId) {
  try {
    const response = await httpClient.post(`/queue/tokens/${tokenId}/customer-cancel`);
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}
