const ACTIVE_QUEUE_STATUSES = new Set(['WAITING', 'CALLED', 'SERVING']);

function normalizeId(value) {
  return value == null || value === '' ? '' : String(value);
}

function getOrderValue(token, fallbackIndex) {
  if (token?.position != null && token.position !== '' && Number.isFinite(Number(token.position))) return Number(token.position);

  const callingTime = token?.calling_time ? new Date(token.calling_time).getTime() : NaN;
  if (!Number.isNaN(callingTime)) return callingTime;

  const createdAt = token?.created_at ? new Date(token.created_at).getTime() : NaN;
  if (!Number.isNaN(createdAt)) return createdAt;

  return fallbackIndex;
}

export function getCheckoutQueueKey(token) {
  if (token?.assigned_counter_id != null && token.assigned_counter_id !== '') return `counter:${normalizeId(token.assigned_counter_id)}`;
  return `section:${normalizeId(token?.store_id)}:${normalizeId(token?.section_id)}`;
}

export function getTrialQueueKey(token) {
  return `zone:${normalizeId(token?.store_id)}:${normalizeId(token?.trial_zone_id)}`;
}

export function isCallable(token, tokens, getQueueKey) {
  if (!token || token.status !== 'WAITING' || typeof getQueueKey !== 'function') return false;

  const queueKey = getQueueKey(token);
  const queueTokens = tokens
    .map((queueToken, index) => ({ token: queueToken, index }))
    .filter(({ token: queueToken }) => ACTIVE_QUEUE_STATUSES.has(queueToken.status) && getQueueKey(queueToken) === queueKey)
    .sort((first, second) => {
      const orderDelta = getOrderValue(first.token, first.index) - getOrderValue(second.token, second.index);
      if (orderDelta !== 0) return orderDelta;
      return Number(first.token?.token_id || 0) - Number(second.token?.token_id || 0);
    });

  const nextWaitingToken = queueTokens.find(({ token: queueToken }) => queueToken.status === 'WAITING')?.token;
  return normalizeId(nextWaitingToken?.token_id) === normalizeId(token.token_id);
}
