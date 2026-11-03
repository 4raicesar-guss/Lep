import { initData } from '@telegram-apps/sdk';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function trackEvent(
  eventName: string,
  payload?: Record<string, unknown>,
): Promise<void> {
  let rawInitData: string | undefined;

  try {
    initData.restore();
    rawInitData = typeof initData.raw === 'function'
      ? initData.raw()
      : String(initData.raw || '');

    if (!rawInitData) {
      rawInitData = undefined;
    }
  } catch {
    // Entorno no-Telegram o SDK no disponible
  }

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
