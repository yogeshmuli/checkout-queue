import {
  ArrowRight,
  Boxes,
  CheckCircle2,
  ShoppingBag,
  Zap,
} from "lucide-react";
import { motion as Motion } from "framer-motion";
import { useNavigate } from "react-router-dom";

import queueHeroSplit from "../../assets/images/queue-hero-split.png";
import { enabledModules, getModuleLoginPath } from "./moduleConfig.js";
import { motionPresets } from "./motionPresets.js";

const moduleIcons = {
  checkout: ShoppingBag,
  trial: Boxes,
};

export function Landing() {
  const navigate = useNavigate();

  return (
    <div className="relative min-h-screen overflow-hidden bg-white font-sans selection:bg-red-100 selection:text-red-900">
      <main className="relative z-10 mx-auto flex min-h-[calc(100vh-96px)] w-full max-w-7xl flex-col items-center justify-center gap-12 px-6 pb-10 pt-6 lg:flex-row lg:gap-20">
        <Motion.section
          {...motionPresets.fadeInLeft}
          className="w-full max-w-2xl"
        >
          {/* <Motion.button
            {...motionPresets.fadeInDown}
            {...motionPresets.subtleButton}
            type="button"
            onClick={() => navigate("/app")}
            className="mb-5 inline-flex items-center gap-2 rounded-xl border border-brand-red/30 bg-white/90 px-4 py-2 text-sm font-semibold text-brand-red shadow-soft hover:bg-white"
          >
            <ScanLine size={16} />
            {showWorkspace ? "Open Workspace" : "Login"}
          </Motion.button> */}

          <Motion.h1
            {...motionPresets.fadeInUp}
            transition={{ ...motionPresets.fadeInUp.transition, delay: 0.2 }}
            className="mb-6 text-[clamp(3.2rem,6vw,5rem)] font-black leading-[1.1] tracking-tight text-slate-900"
          >
            Welcome to <br />
            <span className="relative inline-block text-brand-red">QuT</span>
          </Motion.h1>

          {/* <Motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="mb-10 flex flex-wrap gap-3"
          >
            {badges.map((badge) => (
              <span
                key={badge.text}
                className="flex cursor-default items-center gap-2 rounded-full border border-gray-100 bg-white px-4 py-2 text-sm font-bold text-gray-700 shadow-sm transition-colors hover:border-red-200 hover:text-red-600"
              >
                <badge.Icon size={16} className="text-red-500" />
                {badge.text}
              </span>
            ))}
          </Motion.div> */}

          <Motion.div
            {...motionPresets.fadeInUp}
            transition={{ ...motionPresets.fadeInUp.transition, delay: 0.6 }}
            className="mb-12 space-y-6 text-lg font-medium leading-relaxed text-gray-600"
          >
            <p>
              <strong className="text-slate-900">
                QuT revolutionizes the shopping experience{" "}
              </strong>{" "}
              by ending queues at both trial rooms and checkout counters — one
              scan, zero waiting.
            </p>
            <p>
              Our AI / ML powered intelligent solution revolutionizes queue
              management, reduces manual overhead, and delivers a seamless
              experience for both{" "}
              <strong className="text-slate-900">
                Customer and Store management.
              </strong>
            </p>
            <p>
              Experience faster workflows, real-time tracking, and automatic
              queue balancing — all built for the most happening place in Retail
              i.e. the Store Floor .
            </p>
            <p>
              <strong className="text-slate-900 italic text-[32px]">
                Customer is in the store for shopping not waiting ...
QuT makes customers presence in store matter !
                </strong>
            </p>



          </Motion.div>

          <Motion.div
            {...motionPresets.fadeInUp}
            transition={{ ...motionPresets.fadeInUp.transition, delay: 0.75 }}
            className="mb-10 flex flex-wrap gap-3"
          >
            {enabledModules.map((module) => {
              const Icon = moduleIcons[module.id] || ShoppingBag;
              return (
                <button
                  key={module.id}
                  type="button"
                  onClick={() => navigate(getModuleLoginPath(module.id))}
                  className="inline-flex items-center justify-center gap-3 rounded-2xl bg-brand-red px-6 py-4 text-base font-bold text-white shadow-xl shadow-red-500/25 transition-colors hover:bg-red-600"
                >
                  <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-white/15 text-white">
                    <Icon size={22} />
                  </span>
                  <span>{module.label}</span>
                  <ArrowRight size={18} />
                </button>
              );
            })}
          </Motion.div>

        </Motion.section>

        <Motion.section
          {...motionPresets.heroVisualIn}
          className="relative hidden flex-1 lg:block"
        >
          <div className="relative mx-auto h-[500px] w-[500px]">
            <div className="absolute inset-0 z-20 overflow-hidden rounded-full border-[12px] border-white bg-white shadow-2xl">
              <img
                src={queueHeroSplit}
                alt="Customers waiting in trial room and checkout queues"
                className="h-full w-full object-cover"
              />
              <div className="absolute inset-0 flex items-center justify-center bg-white/10">
                <svg
                  viewBox="0 0 100 100"
                  role="img"
                  aria-label="No waiting allowed"
                  className="h-40 w-40 animate-pulse drop-shadow-2xl"
                >
                  <circle
                    cx="50"
                    cy="50"
                    r="38"
                    fill="none"
                    stroke="#dc2626"
                    strokeWidth="12"
                  />
                  <line
                    x1="25"
                    y1="75"
                    x2="75"
                    y2="25"
                    stroke="#dc2626"
                    strokeWidth="12"
                    strokeLinecap="round"
                  />
                  <circle
                    cx="50"
                    cy="50"
                    r="44"
                    fill="none"
                    stroke="#111827"
                    strokeWidth="2"
                    opacity="0.8"
                  />
                </svg>
              </div>
            </div>

            {/* <Motion.div {...motionPresets.floatUpDown} className="absolute -right-10 -top-10 z-30 rounded-3xl border border-gray-100 bg-white p-4 shadow-xl">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-100 text-green-600">
                  <CheckCircle2 size={22} />
                </div>
                <div>
                  <div className="text-xs font-bold uppercase text-gray-400">Status</div>
                  <div className="text-sm font-black text-slate-800">Live</div>
                </div>
              </div>
            </Motion.div> */}

            {/* <Motion.div {...motionPresets.floatDownUp} className="absolute -bottom-5 -left-5 z-30 rounded-3xl border border-gray-100 bg-white p-4 shadow-xl">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-red-100 text-red-600">
                  <Zap size={22} />
                </div>
                <div>
                  <div className="text-xs font-bold uppercase text-gray-400">Speed</div>
                  <div className="text-sm font-black text-slate-800">Instant</div>
                </div>
              </div>
            </Motion.div> */}

            <div className="absolute inset-0 z-0 scale-110 rounded-full bg-red-500 opacity-20 blur-[100px]" />
          </div>
        </Motion.section>
      </main>
    </div>
  );
}
