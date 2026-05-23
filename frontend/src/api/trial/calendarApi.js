import { httpClient } from '../httpClient.js';
import { trialRequest } from './request.js';

export function getTrialCalendar(storeId) {
  return trialRequest(() => httpClient.get(`/stores/${storeId}/trial-calendar`));
}

export function updateTrialCalendar(storeId, payload) {
  return trialRequest(() => httpClient.put(`/stores/${storeId}/trial-calendar`, payload));
}
