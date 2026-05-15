import { httpClient } from './httpClient.js';

export function listStores(params = {}) {
  return httpClient.get('/stores', { params }).then((response) => response.data);
}

export function createStore(payload) {
  return httpClient.post('/stores', payload).then((response) => response.data);
}

export function updateStore(storeId, payload) {
  return httpClient.patch(`/stores/${storeId}`, payload).then((response) => response.data);
}

export function deleteStore(storeId) {
  return httpClient.delete(`/stores/${storeId}`).then((response) => response.data);
}

