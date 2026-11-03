import { useState, useEffect } from 'react';
import { initData } from '@telegram-apps/sdk';
import { trackEvent } from './analytics';
import { BattlePage } from './pages/BattlePage';

type AuthState =
  | { status: 'loading' }
  | { status: 'ok'; user: { first_name: string; username?: string } }
  | { status: 'error'; message: string };

function App() {
  const [auth, setAuth] = useState<AuthState>({ status: 'loading' });
  const [view, setView] = useState<'combat' | 'home'>('combat');

  useEffect(() => {
    const authenticate = async () => {
      try {
        initData.restore();
        const raw = typeof initData.raw === 'function' ? initData.raw() : (initData.raw as unknown as string);

        if (!raw) {
          setAuth({ status: 'error', message: 'No initData disponible. Abre desde Telegram.' });
          return;
        }

        const res = await fetch('http://localhost:8000/auth/telegram', {
          method: 'POST',
          headers: { 'X-Telegram-Init-Data': raw },
        });

        if (!res.ok) {
          const body = await res.json();
          setAuth({ status: 'error', message: body.detail || 'Error de autenticación' });
          return;
        }

        const data = await res.json();
        setAuth({ status: 'ok', user: data.user });
      } catch (err) {
        setAuth({ status: 'error', message: String(err) });
      }
    };

    authenticate();
  }, []);

  const handleTestEvent = () => {
    trackEvent('test_button_click', { screen: 'home' });
  };

  return (
    <div className="min-h-screen bg-stone-950 text-stone-100 flex flex-col items-center justify-start p-4">
      {/* Barra de navegación rápida */}
      <div className="w-full max-w-md flex justify-between items-center mb-4 bg-stone-900/80 p-2 rounded-xl border border-stone-800">
        <div className="text-sm font-bold text-amber-400">🌾 Granja Táctica</div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setView('combat')}
            className={`px-3 py-1 text-xs font-semibold rounded-lg transition ${
              view === 'combat' ? 'bg-amber-500 text-stone-950' : 'bg-stone-800 text-stone-300'
            }`}
          >
            ⚔️ Combate
          </button>
          <button
            type="button"
            onClick={() => setView('home')}
            className={`px-3 py-1 text-xs font-semibold rounded-lg transition ${
              view === 'home' ? 'bg-amber-500 text-stone-950' : 'bg-stone-800 text-stone-300'
            }`}
          >
            🏠 Estado
          </button>
        </div>
      </div>

      {view === 'combat' ? (
        <BattlePage />
      ) : (
        <div className="flex flex-col items-center justify-center gap-4 mt-8">
          {auth.status === 'loading' && <div className="text-lg">Cargando...</div>}
          {auth.status === 'error' && <p className="text-red-500 text-lg">{auth.message}</p>}
          {auth.status === 'ok' && (
            <h1 className="text-2xl font-bold">
              🌾 Bienvenido, {auth.user.first_name}
              {auth.user.username && <span className="text-gray-500 font-normal"> @{auth.user.username}</span>}
            </h1>
          )}
          <button
            type="button"
            onClick={handleTestEvent}
            className="px-4 py-2 font-semibold text-white bg-blue-600 rounded-md hover:bg-blue-700 transition"
          >
            Probar Evento
          </button>
        </div>
      )}
    </div>
  );
}

export default App;

