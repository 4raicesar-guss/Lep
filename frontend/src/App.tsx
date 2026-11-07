import { useState, useEffect } from 'react';
import { getTelegramInitData, API_BASE_URL } from './lib/api';
import type { View } from './lib/game';
import { trackEvent } from './analytics';

import { HomePage } from './pages/HomePage';
import { MergePage } from './pages/MergePage';
import { FormationPage } from './pages/FormationPage';
import { BattlePage } from './pages/BattlePage';

interface AuthUser {
  first_name: string;
  username?: string;
  id?: number;
}

type AuthState =
  | { status: 'loading' }
  | { status: 'ok'; user: AuthUser }
  | { status: 'guest'; message?: string };

export function App() {
  const [view, setView] = useState<View>('home');
  const [auth, setAuth] = useState<AuthState>({ status: 'loading' });

  // Autenticación inicial con Telegram
  useEffect(() => {
    const authenticate = async () => {
      try {
        const raw = getTelegramInitData();

        if (!raw) {
          setAuth({ status: 'guest', message: 'Navegador Web / Modo Local' });
          return;
        }

        const res = await fetch(`${API_BASE_URL}/auth/telegram`, {
          method: 'POST',
          headers: { 'X-Telegram-Init-Data': raw },
        });

        if (!res.ok) {
          setAuth({ status: 'guest', message: 'Sesión local' });
          return;
        }

        const data = await res.json();
        setAuth({ status: 'ok', user: data.user });
      } catch {
        setAuth({ status: 'guest', message: 'Conexión local' });
      }
    };

    authenticate();
  }, []);

  const handleNavigate = (newView: View) => {
    setView(newView);
    trackEvent('page_view', { page: newView });
  };

  return (
    <div className="min-h-screen bg-stone-950 text-stone-100 flex flex-col items-center justify-start p-4 pb-24">
      {/* Cabecera Superior de la Mini App */}
      <header className="w-full max-w-md flex justify-between items-center mb-4 bg-stone-900/90 px-4 py-2.5 rounded-2xl border border-stone-800 shadow-lg">
        <div className="flex items-center gap-2">
          <span className="text-xl">🌾</span>
          <div>
            <h1 className="text-sm font-black text-amber-400 tracking-wide">Granja Táctica</h1>
            <span className="text-[10px] text-stone-400 block leading-none">
              {auth.status === 'ok' ? (
                <span>
                  👨‍🌾 {auth.user.first_name}
                  {auth.user.username && <span className="text-stone-500"> (@{auth.user.username})</span>}
                </span>
              ) : auth.status === 'guest' ? (
                <span className="text-amber-500/80">🌐 {auth.message}</span>
              ) : (
                'Conectando…'
              )}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-[10px] font-mono font-bold text-stone-400">Core Loop v1.0</span>
        </div>
      </header>

      {/* Pantalla Activa */}
      <main className="w-full max-w-md flex-1 flex flex-col items-center">
        {view === 'home' && <HomePage onNavigate={handleNavigate} />}
        {view === 'merge' && <MergePage onNavigate={handleNavigate} />}
        {view === 'formation' && <FormationPage onNavigate={handleNavigate} />}
        {view === 'battle' && <BattlePage onNavigate={handleNavigate} />}
      </main>

      {/* Barra de Navegación Inferior Fija (Telegram Mini App Style) */}
      <nav className="fixed bottom-0 inset-x-0 bg-stone-900/95 backdrop-blur-md border-t border-stone-800/90 py-1.5 px-3 z-40 max-w-md mx-auto shadow-2xl">
        <div className="grid grid-cols-4 gap-1">
          <button
            type="button"
            onClick={() => handleNavigate('home')}
            className={`flex flex-col items-center justify-center py-1 px-1 rounded-xl transition-all ${
              view === 'home'
                ? 'bg-amber-500/15 text-amber-400 font-bold scale-105'
                : 'text-stone-400 hover:text-stone-200'
            }`}
          >
            <span className="text-lg">🏠</span>
            <span className="text-[11px] mt-0.5">Granja</span>
          </button>

          <button
            type="button"
            onClick={() => handleNavigate('merge')}
            className={`flex flex-col items-center justify-center py-1 px-1 rounded-xl transition-all ${
              view === 'merge'
                ? 'bg-amber-500/15 text-amber-400 font-bold scale-105'
                : 'text-stone-400 hover:text-stone-200'
            }`}
          >
            <span className="text-lg">🔄</span>
            <span className="text-[11px] mt-0.5">Merge</span>
          </button>

          <button
            type="button"
            onClick={() => handleNavigate('formation')}
            className={`flex flex-col items-center justify-center py-1 px-1 rounded-xl transition-all ${
              view === 'formation'
                ? 'bg-amber-500/15 text-amber-400 font-bold scale-105'
                : 'text-stone-400 hover:text-stone-200'
            }`}
          >
            <span className="text-lg">⚔️</span>
            <span className="text-[11px] mt-0.5">Formación</span>
          </button>

          <button
            type="button"
            onClick={() => handleNavigate('battle')}
            className={`flex flex-col items-center justify-center py-1 px-1 rounded-xl transition-all ${
              view === 'battle'
                ? 'bg-amber-500/15 text-amber-400 font-bold scale-105'
                : 'text-stone-400 hover:text-stone-200'
            }`}
          >
            <span className="text-lg">💥</span>
            <span className="text-[11px] mt-0.5">Batalla</span>
          </button>
        </div>
      </nav>
    </div>
  );
}

export default App;
