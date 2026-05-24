import { httpClient, normalizeApiError } from './httpClient.js';

export async function getDemoMlTrainingDataStatus() {
  try {
    const response = await httpClient.get('/demotools/ml-training-data/status');
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function seedDemoMlTrainingData({ replace = false } = {}) {
  try {
    const response = await httpClient.post('/demotools/ml-training-data', null, { params: { replace } });
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function cleanDemoMlTrainingData() {
  try {
    const response = await httpClient.delete('/demotools/ml-training-data');
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}
