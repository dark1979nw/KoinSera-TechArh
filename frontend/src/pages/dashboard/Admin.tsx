import { useAuth } from '../../contexts/AuthContext';
import { Navigate } from 'react-router-dom';
import AdminPanel from '../../components/dashboard/AdminPanel';

export default function Admin() {
  const { user } = useAuth();

  if (!user?.is_admin) {
    return <Navigate to="/dashboard" replace />;
  }

  return <AdminPanel />;
} 