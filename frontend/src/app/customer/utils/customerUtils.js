export const defaultForm = {
  store_id: '1',
  section_id: '1',
  phone_number: '',
  item_count: '8',
  basket_size: 'medium',
  cart_type: 'basket',
  is_still_shopping: true,
  customer_type: 'regular',
};

export const TOKEN_STATUS_REFRESH_MS = 30000;

export function getWaitMinutes(callingTime) {
  if (!callingTime) return 0;
  const diffMs = new Date(callingTime).getTime() - Date.now();
  return Math.max(0, Math.ceil(diffMs / 60000));
}

export function formatTime(value) {
  if (!value) return 'Not scheduled';
  return new Intl.DateTimeFormat(undefined, {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }).format(new Date(value));
}
