import React, { useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const AuthCallback: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { refreshUser } = useAuth();
  const called = useRef(false);

  useEffect(() => {
    if (called.current) return;
    called.current = true;

    const code = searchParams.get('code');
    if (!code) {
      navigate('/login?error=auth_failed', { replace: true });
      return;
    }

    fetch(`/api/auth/exchange?code=${encodeURIComponent(code)}`)
      .then(async (res) => {
        if (!res.ok) {
          navigate('/login?error=auth_failed', { replace: true });
          return;
        }
        const data = await res.json();
        sessionStorage.setItem('access_token', data.token);
        await refreshUser();
        navigate('/dashboard', { replace: true });
      })
      .catch(() => {
        navigate('/login?error=auth_failed', { replace: true });
      });
  }, []);

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-900">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto" />
        <p className="mt-4 text-gray-400">Signing in…</p>
      </div>
    </div>
  );
};

export default AuthCallback;
