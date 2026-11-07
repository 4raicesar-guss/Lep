import { getTelegramInitData, API_BASE_URL } from './lib/api';

export async function trackEvent(
  eventName: string,
  payload?: Record<string, unknown>,
): Promise<void> {
  const rawInitData = getTelegramInitData();

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (rawInitData) {
    headers['X-Telegram-Init-Data'] = rawInitData;
  }

  const url = `${API_BASE_URL}/api/analytics/event`;

  const body = JSON.stringify({
    event_name: eventName,
    payload: payload ?? {},
  });

  try {
    await fetch(url, {
      method: 'POST',
      headers,
      body,
      keepalive: true,
    });
  } catch (error) {
    console.warn('Error al enviar evento de analítica:', error);
  }
}
