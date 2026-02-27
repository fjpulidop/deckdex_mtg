import { Navigate } from 'react-router-dom';

// Settings content has been moved to SettingsModal.tsx (accessed from the user dropdown in Navbar).
export function Settings() {
  return <Navigate to="/dashboard" replace />;
}
