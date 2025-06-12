import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  List,
  Typography,
  Divider,
  IconButton,
  ListItem,
  ListItemIcon,
  ListItemText,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  Menu as MenuIcon,
  ChevronLeft as ChevronLeftIcon,
  Dashboard as DashboardIcon,
  Person as PersonIcon,
  ShoppingCart as ShoppingCartIcon,
  AccountBalanceWallet as AccountBalanceWalletIcon,
  Settings as SettingsIcon,
  AdminPanelSettings as AdminPanelSettingsIcon,
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';

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
      path: '/dashboard/personal-info',
    },
    {
      text: t('dashboard.navigation.bots'),
      icon: <ShoppingCartIcon />,
      path: '/dashboard/orders',
    },
    {
      text: t('dashboard.navigation.profile'),
      icon: <AccountBalanceWalletIcon />,
      path: '/dashboard/wallet',
    },
    {
      text: t('dashboard.navigation.finance'),
      icon: <SettingsIcon />,
      path: '/dashboard/settings',
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
    <Box sx={{ display: 'flex' }}>
      <AppBar position="fixed">
        <Toolbar>
          <IconButton
            color="inherit"
            edge="start"
            onClick={() => setOpen(!open)}
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div">
            {t('dashboard.title')}
          </Typography>
        </Toolbar>
      </AppBar>
      <Drawer
        variant={isMobile ? 'temporary' : 'permanent'}
        open={open}
        onClose={() => setOpen(false)}
      >
        <Box sx={{ width: 240 }}>
          <IconButton onClick={() => setOpen(false)}>
            <ChevronLeftIcon />
          </IconButton>
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
        </Box>
      </Drawer>
      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        <Toolbar />
        {children}
      </Box>
    </Box>
  );
};

export default Dashboard; 