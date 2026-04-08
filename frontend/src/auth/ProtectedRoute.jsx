import { Navigate, useLocation } from "react-router-dom";

import { useAuth } from "./AuthContext.jsx";

export default function ProtectedRoute({ children }) {
  const { authReady, user } = useAuth();
  const location = useLocation();

  if (!authReady) {
    return <div className="loading-state">Connecting to Firebase authentication...</div>;
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return children;
}
