import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Drawer,
  List,
  Divider,
  ListItem,
  ListItemIcon,
  ListItemText,
  useTheme,
  useMediaQuery,
  Toolbar,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Person as PersonIcon,
  SmartToy as SmartToyIcon,
  AccountBalanceWallet as AccountBalanceWalletIcon,
  Settings as SettingsIcon,
  AdminPanelSettings as AdminPanelSettingsIcon,
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import Header from './Header';

const drawerWidth = 240;

const Dashboard: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const isAdmin = user?.is_admin || false;
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [open, setOpen] = useState(!isMobile);
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    {
      text: t('dashboard.navigation.chats'),
      icon: <DashboardIcon />,
      path: '/dashboard',
    },
    {
      text: t('dashboard.navigation.users'),
      icon: <PersonIcon />,
      path: '/dashboard/users',
    },
    {
      text: t('dashboard.navigation.bots'),
      icon: <SmartToyIcon />,
      path: '/dashboard/bots',
    },
    {
      text: t('dashboard.navigation.profile'),
      icon: <AccountBalanceWalletIcon />,
      path: '/dashboard/profile',
    },
    {
      text: t('dashboard.navigation.finance'),
      icon: <SettingsIcon />,
      path: '/dashboard/finance',
    },
    ...(isAdmin
      ? [
          {
            text: t('dashboard.navigation.admin'),
            icon: <AdminPanelSettingsIcon />,
            path: '/dashboard/admin',
          },
        ]
      : []),
  ];

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      {/* Header with user info and logout */}
      <Header />
      {/* Drawer (sidebar) */}
      <Drawer
        variant={isMobile ? 'temporary' : 'permanent'}
        open={open}
        onClose={() => setOpen(false)}
        sx={{
          width: drawerWidth ,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
            position: 'fixed',
            height: '100vh',
            zIndex: (theme) => theme.zIndex.appBar - 1,
          },
        }}
      >
        <Toolbar />
        <Divider />
        <List>
          {menuItems.map((item) => (
            <ListItem
              button
              key={item.path}
              onClick={() => navigate(item.path)}
              selected={location.pathname === item.path}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItem>
          ))}
        </List>
      </Drawer>
      {/* Main content with correct margin for header and drawer */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: '64px',
          mt: '64px', // AppBar height
          overflow: 'auto',
        }}
      >
        {children}
      </Box>
    </Box>
  );
};

export default Dashboard; 