import { ArrowRight, Boxes, CheckCircle2, ScanLine, ShoppingBag, Star, Zap } from 'lucide-react';
import { motion as Motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

import { useAuthStore } from '../../store/authStore.js';
import { enabledModules } from './moduleConfig.js';
import { motionPresets } from './motionPresets.js';

const badges = [
  { text: 'Zero Queue Waiting', Icon: CheckCircle2 },
  { text: 'Fast Checkout Flow', Icon: Zap },
  { text: 'Reliable Operations', Icon: Star },
];

const moduleIcons = {
  checkout: ShoppingBag,
  trial: Boxes,
};

export function Landing() {
  const navigate = useNavigate();
  const { accessToken, user } = useAuthStore();

  const showWorkspace = Boolean(accessToken && user);

  return (
    <div className="relative min-h-screen overflow-hidden bg-white font-sans selection:bg-red-100 selection:text-red-900">

      <main className="relative z-10 mx-auto flex min-h-[calc(100vh-96px)] w-full max-w-7xl flex-col items-center justify-center gap-12 px-6 pb-10 pt-6 lg:flex-row lg:gap-20">
        <Motion.section {...motionPresets.fadeInLeft} className="w-full max-w-2xl">
          <Motion.button
            {...motionPresets.fadeInDown}
            {...motionPresets.subtleButton}
            type="button"
            onClick={() => navigate('/app')}
            className="mb-5 inline-flex items-center gap-2 rounded-xl border border-brand-red/30 bg-white/90 px-4 py-2 text-sm font-semibold text-brand-red shadow-soft hover:bg-white"
          >
            <ScanLine size={16} />
            {showWorkspace ? 'Open Workspace' : 'Login'}
          </Motion.button>

          <Motion.h1
            {...motionPresets.fadeInUp}
            transition={{ ...motionPresets.fadeInUp.transition, delay: 0.2 }}
            className="mb-6 text-[clamp(3.2rem,6vw,5rem)] font-black leading-[1.1] tracking-tight text-slate-900"
          >
            Welcome to <br />
            <span className="relative inline-block text-brand-red">
              QuT
            
            </span>
          </Motion.h1>

          <Motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="mb-10 flex flex-wrap gap-3"
          >
            {badges.map((badge) => (
              <span key={badge.text} className="flex cursor-default items-center gap-2 rounded-full border border-gray-100 bg-white px-4 py-2 text-sm font-bold text-gray-700 shadow-sm transition-colors hover:border-red-200 hover:text-red-600">
                <badge.Icon size={16} className="text-red-500" />
                {badge.text}
              </span>
            ))}
          </Motion.div>

          <Motion.div
            {...motionPresets.fadeInUp}
            transition={{ ...motionPresets.fadeInUp.transition, delay: 0.6 }}
            className="mb-12 space-y-6 text-lg font-medium leading-relaxed text-gray-600"
          >
            <p>
              <strong className="text-slate-900">One workspace now supports two queue modules</strong> for different store operations.
            </p>
            <p>
              Checkout Queue manages billing counters, customer tokens, and live store traffic.
            </p>
            <p>
              Trial Queue manages trial zones, studios, and fitting-room style customer movement.
            </p>
          </Motion.div>

          <Motion.div
            {...motionPresets.fadeInUp}
            transition={{ ...motionPresets.fadeInUp.transition, delay: 0.75 }}
            className="mb-10 grid gap-3 sm:grid-cols-2"
          >
            {enabledModules.map((module) => {
              const Icon = moduleIcons[module.id] || ShoppingBag;
              return (
                <div key={module.id} className="rounded-xl border border-gray-100 bg-white p-4 shadow-sm">
                  <div className="mb-3 flex h-11 w-11 items-center justify-center rounded-lg bg-brand-blush text-brand-red">
                    <Icon size={22} />
                  </div>
                  <h2 className="text-lg font-bold text-slate-900">{module.label}</h2>
                  <p className="mt-1 text-sm leading-6 text-gray-600">{module.description}</p>
                </div>
              );
            })}
          </Motion.div>

          <Motion.button
            {...motionPresets.buttonSpring}
            type="button"
            onClick={() => navigate('/app')}
            className="group relative overflow-hidden rounded-2xl bg-brand-red px-8 py-4 text-lg font-bold text-white shadow-xl shadow-red-500/30"
          >
            <span className="relative z-10 flex items-center gap-2">
              Open Workspace
              <ArrowRight size={20} className="transition-transform duration-300 group-hover:translate-x-1" />
            </span>
            <div className="absolute inset-0 origin-left scale-x-0 bg-red-600 transition-transform duration-300 group-hover:scale-x-100" />
          </Motion.button>
        </Motion.section>

        <Motion.section {...motionPresets.heroVisualIn} className="relative hidden flex-1 lg:block">
          <div className="relative mx-auto h-[500px] w-[500px]">
            <div className="absolute inset-0 z-20 overflow-hidden rounded-full border-[12px] border-white bg-brand-red shadow-2xl">
              <div className="flex h-full items-center justify-center">
                <div className="rounded-3xl bg-white/90 px-10 py-8 text-center text-ink shadow-brand">
                  <p className="text-xs font-semibold uppercase tracking-wide text-muted">Realtime Queue</p>
                  <p className="mt-2 text-3xl font-black text-brand-red">Optimized</p>
                </div>
              </div>
            </div>

            <Motion.div {...motionPresets.floatUpDown} className="absolute -right-10 -top-10 z-30 rounded-3xl border border-gray-100 bg-white p-4 shadow-xl">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-100 text-green-600">
                  <CheckCircle2 size={22} />
                </div>
                <div>
                  <div className="text-xs font-bold uppercase text-gray-400">Status</div>
                  <div className="text-sm font-black text-slate-800">Live</div>
                </div>
              </div>
            </Motion.div>

            <Motion.div {...motionPresets.floatDownUp} className="absolute -bottom-5 -left-5 z-30 rounded-3xl border border-gray-100 bg-white p-4 shadow-xl">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-red-100 text-red-600">
                  <Zap size={22} />
                </div>
                <div>
                  <div className="text-xs font-bold uppercase text-gray-400">Speed</div>
                  <div className="text-sm font-black text-slate-800">Instant</div>
                </div>
              </div>
            </Motion.div>

            <div className="absolute inset-0 z-0 scale-110 rounded-full bg-red-500 opacity-20 blur-[100px]" />
          </div>
        </Motion.section>
      </main>
    </div>
  );
}
