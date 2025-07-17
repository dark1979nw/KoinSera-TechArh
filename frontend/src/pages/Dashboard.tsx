//import { useTranslation } from 'react-i18next';
import { Routes, Route, Navigate } from 'react-router-dom';
import DashboardLayout from '../components/dashboard/Dashboard';
import Admin from './dashboard/Admin';
import BotsPanel from '../components/dashboard/BotsPanel';
import ChatsPanel from '../components/dashboard/ChatsPanel';
import UsersPanel from '../components/dashboard/UsersPanel';
import Profile from './Profile';

// Placeholder components for each section
const Chats = () => <ChatsPanel />;
const Users = () => <UsersPanel />;
const Finance = () => <div>Finance Page</div>;

export default function Dashboard() {
 // const { t } = useTranslation();

  return (
    <DashboardLayout>
      <Routes>
        <Route path="/" element={<Navigate to="chats" replace />} />
        <Route path="chats" element={<Chats />} />
        <Route path="users" element={<Users />} />
        <Route path="bots" element={<BotsPanel />} />
        <Route path="profile" element={<Profile />} />
        <Route path="finance" element={<Finance />} />
        <Route path="admin" element={<Admin />} />
      </Routes>
    </DashboardLayout>
  );
} 