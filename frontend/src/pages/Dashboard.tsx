//import { useTranslation } from 'react-i18next';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Box, CssBaseline, Drawer, Toolbar } from '@mui/material';
import Header from '../components/dashboard/Header';
import Navigation from '../components/dashboard/Navigation';
import Admin from './dashboard/Admin';

// Placeholder components for each section
const Chats = () => <div>Chats Page</div>;
const Users = () => <div>Users Page</div>;
const Bots = () => <div>Bots Page</div>;
const Profile = () => <div>Profile Page</div>;
const Finance = () => <div>Finance Page</div>;

const drawerWidth = 240;

export default function Dashboard() {
 // const { t } = useTranslation();

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      <Header />
      <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
          },
        }}
      >
        <Toolbar /> {/* This creates space for the fixed header */}
        <Navigation />
      </Drawer>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
        }}
      >
        <Toolbar /> {/* This creates space for the fixed header */}
        <Routes>
          <Route path="/" element={<Navigate to="chats" replace />} />
          <Route path="chats" element={<Chats />} />
          <Route path="users" element={<Users />} />
          <Route path="bots" element={<Bots />} />
          <Route path="profile" element={<Profile />} />
          <Route path="finance" element={<Finance />} />
          <Route path="admin" element={<Admin />} />
        </Routes>
      </Box>
    </Box>
  );
} 