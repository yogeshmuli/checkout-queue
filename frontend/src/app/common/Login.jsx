import { LogIn } from 'lucide-react';
import { useState } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';

import brandLogo from '../../assets/images/equilateral_logo.png';
import { loginUser } from '../../api/authApi.js';
import { getErrorMessage, showApiErrorToast } from '../../api/httpClient.js';
import { useAuthStore } from '../../store/authStore.js';
import { getModuleHomePath } from './moduleConfig.js';
import { getUserScope } from './roleUtils.js';
import {FaEye,FaEyeSlash} from "react-icons/fa"

const LOGIN_CONTEXT = {
  checkout: {
    eyebrow: 'Queueless Transaction',
    logoAlt: 'Queueless Transaction logo',
  },
  trial: {
    eyebrow: 'Quick Trial',
    logoAlt: 'Quick Trial logo',
  },
  default: {
    eyebrow: 'QuT Workspace',
    logoAlt: 'QuT logo',
  },
};

export function Login({ moduleId = null }) {
  const navigate = useNavigate();
  const { accessToken, user, setSession } = useAuthStore();
  const [form, setForm] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const context = LOGIN_CONTEXT[moduleId] || LOGIN_CONTEXT.default;
  
  const redirectPath = user && moduleId ? getModuleHomePath(moduleId, getUserScope(user)) : '/app';

  if (accessToken && user) {
    return <Navigate to={redirectPath} replace />;
  }

  async function submitLogin(event) {
    event.preventDefault();
    setLoading(true);
    setMessage('');
    try {
      const session = await loginUser(form);
      setSession(session);
      const scope = getUserScope(session.user);
      navigate(moduleId ? getModuleHomePath(moduleId, scope) : '/app', { replace: true });
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }
  const togglePasswordVisibility = () => {
    setShowPassword((prevState) => !prevState);
  }

  return (
    <main className="min-h-screen bg-brand-blush px-4 py-5 text-ink animate-fadeIn">
      <section className="mx-auto flex min-h-screen max-w-md flex-col justify-center animate-slideUp">
        <header className="rounded-lg bg-brand-red px-4 py-3 text-white shadow-brand">
          <div className="flex items-center gap-3">
            <img src={brandLogo} alt={context.logoAlt} className="h-10 w-24 rounded-lg bg-white p-1 object-cover" />
            <div>
              <p className="text-xs text-red-100">{context.eyebrow}</p>
              <h1 className="text-2xl font-semibold text-white">Sign in</h1>
            </div>
          </div>
        </header>

        <form className="mt-5 space-y-3 rounded-lg bg-white p-4 text-ink shadow-soft" onSubmit={submitLogin}>
          <label className="block">
            <span className="text-sm font-medium text-charcoal">Email</span>
            <input
              value={form.email}
              onChange={(event) => setForm({ ...form, email: event.target.value })}
              className="mt-1 w-full rounded-lg border border-line px-3 py-2.5 outline-none focus:border-brand-red"
            />
          </label>
          <label className="block">
            <span className="text-sm font-medium text-charcoal">Password</span>
          <div className="mt-1 flex w-full items-center rounded-lg border border-line px-3 py-2.5 outline-none focus-within:border-brand-red">
              <input
              type={showPassword ? 'text' : 'password'}
              value={form.password}
              onChange={(event) => setForm({ ...form, password: event.target.value })}
              className="flex-1 outline-none"
            
            />
            <button
              type="button"
              onClick={togglePasswordVisibility}
              className=" text-charcoal"
            >
              {showPassword ? <FaEyeSlash title="Hide password" /> : <FaEye title="Show password" />}
            </button>
          </div>
          </label>
          {message ? <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{message}</p> : null}
          <button type="submit" disabled={loading} className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-brand-red px-4 py-3 text-sm font-semibold text-white disabled:opacity-60">
            <LogIn size={18} />
            Login
          </button>
          {/* <Link to="/app/checkout/customer" className="inline-flex w-full items-center justify-center gap-2 rounded-lg border border-brand-red/30 bg-brand-blush px-4 py-3 text-sm font-medium text-brand-red">
            <ScanLine size={18} />
            Continue as checkout customer
          </Link>
          <Link to="/app/trial/customer" className="inline-flex w-full items-center justify-center gap-2 rounded-lg border border-brand-red/30 bg-brand-blush px-4 py-3 text-sm font-medium text-brand-red">
            <ScanLine size={18} />
            Continue as trial customer
          </Link> */}
        </form>
      </section>
    </main>
  );
}
