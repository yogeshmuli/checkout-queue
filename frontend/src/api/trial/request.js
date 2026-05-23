import { normalizeApiError } from '../httpClient.js';

export async function trialRequest(fn) {
  try {
    const response = await fn();
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}
