import axios from 'axios';
import { toast } from 'react-toastify';

import { useAuthStore } from '../store/authStore.js';

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim() || '/api/v1';

export const httpClient = axios.create({
  baseURL: apiBaseUrl,
  timeout: 15000,
});

let isRedirectingToLogin = false;

httpClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

httpClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const statusCode = error?.response?.status;
    const { accessToken, clearSession } = useAuthStore.getState();

    if (statusCode === 401 && accessToken) {
      clearSession();

      if (!isRedirectingToLogin && window.location.pathname !== '/app/login') {
        isRedirectingToLogin = true;
        window.location.replace('/app/login');
      }
    }

    return Promise.reject(error);
  }
);

export function getErrorMessage(error) {
  const detail = error?.response?.data?.detail;
  const fallbackMessage = error?.message;

  if (typeof detail === 'string' && detail.trim()) {
    return detail;
  }

  if (Array.isArray(detail)) {
    const combined = detail
      .map((item) => {
        if (typeof item === 'string') return item;
        if (item && typeof item === 'object') {
          if (typeof item.msg === 'string') return item.msg;
          if (typeof item.message === 'string') return item.message;
          return JSON.stringify(item);
        }
        return '';
      })
      .filter(Boolean)
      .join(', ');

    if (combined) return combined;
  }

  if (detail && typeof detail === 'object') {
    if (typeof detail.message === 'string' && detail.message.trim()) {
      return detail.message;
    }
    if (typeof detail.msg === 'string' && detail.msg.trim()) {
      return detail.msg;
    }
    try {
      return JSON.stringify(detail);
    } catch {
      return 'Something went wrong';
    }
  }

  if (typeof fallbackMessage === 'string' && fallbackMessage.trim()) {
    return fallbackMessage;
  }

  return 'Something went wrong';
}

export function normalizeApiError(error) {
  const normalizedError = new Error(getErrorMessage(error));
  normalizedError.status = error?.response?.status || null;
  normalizedError.detail = error?.response?.data?.detail || null;
  normalizedError.originalError = error;
  return normalizedError;
}

export function showApiErrorToast(error) {
  const message = getErrorMessage(error);
  toast.error(message, { toastId: `api-error-${message}` });
}

