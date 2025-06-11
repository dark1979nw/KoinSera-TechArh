import { useTranslation } from 'react-i18next';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
} from '@mui/material';
import {
  Chat as ChatIcon,
  People as PeopleIcon,
  SmartToy as BotIcon,
  Person as PersonIcon,
  AccountBalance as FinanceIcon,
  AdminPanelSettings as AdminIcon,
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';

const menuItems = [
  { path: 'chats', icon: <ChatIcon />, translationKey: 'dashboard.navigation.chats' },
  { path: 'users', icon: <PeopleIcon />, translationKey: 'dashboard.navigation.users' },
  { path: 'bots', icon: <BotIcon />, translationKey: 'dashboard.navigation.bots' },
  { path: 'profile', icon: <PersonIcon />, translationKey: 'dashboard.navigation.profile' },
  { path: 'finance', icon: <FinanceIcon />, translationKey: 'dashboard.navigation.finance' },
];

const adminMenuItem = {
  path: 'admin',
  icon: <AdminIcon />,
  translationKey: 'dashboard.navigation.admin',
};

export default function Navigation() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();

  const allMenuItems = user?.is_admin ? [...menuItems, adminMenuItem] : menuItems;

  return (
    <List component="nav" sx={{ width: 240, bgcolor: 'background.paper' }}>
      {allMenuItems.map((item) => (
        <ListItem key={item.path} disablePadding>
          <ListItemButton
            selected={location.pathname === `/dashboard/${item.path}`}
            onClick={() => navigate(item.path)}
          >
            <ListItemIcon>{item.icon}</ListItemIcon>
            <ListItemText primary={t(item.translationKey)} />
          </ListItemButton>
        </ListItem>
      ))}
    </List>
  );
} 