import { useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";

export default function LoginPage() {
  const { signInWithGoogle } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  async function handleLogin() {
    await signInWithGoogle();
    navigate(location.state?.from?.pathname || "/", { replace: true });
  }

  return (
    <div className="login-shell">
      <section className="login-panel">
        <span className="eyebrow">Production-Grade Estimation</span>
        <h1>Secure AWS Cost Modeling</h1>
        <p>
          Sign in with Firebase to access authenticated estimation, compare scenarios, and
          optimization guidance.
        </p>
        <button type="button" className="primary-button" onClick={handleLogin}>
          Sign in with Google
        </button>
      </section>
    </div>
  );
}

