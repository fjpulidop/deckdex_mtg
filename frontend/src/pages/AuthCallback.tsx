import React, { useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';

const AuthCallback: React.FC = () => {
  const { t } = useTranslation();
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

    // Exchange the one-time code — backend sets HTTP-only cookie automatically
    fetch(`/api/auth/exchange?code=${encodeURIComponent(code)}`, {
      credentials: 'include',
    })
      .then(async (res) => {
        if (!res.ok) {
          navigate('/login?error=auth_failed', { replace: true });
          return;
        }
        // Cookie is set by the backend; just refresh user state
        await refreshUser();
        navigate('/dashboard', { replace: true });
      })
      .catch(() => {
        navigate('/login?error=auth_failed', { replace: true });
      });
  // eslint-disable-next-line react-hooks/exhaustive-deps -- only run once on mount (auth exchange)
  }, []);

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-900">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto" />
        <p className="mt-4 text-gray-400">{t('login.loading')}</p>
      </div>
    </div>
  );
};

export default AuthCallback;
