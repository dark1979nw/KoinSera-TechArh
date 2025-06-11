import { Box, Container, Typography, Button, AppBar, Toolbar } from '@mui/material';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext.tsx';
import { Logout } from '@mui/icons-material';

export default function Home() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { user, isAuthenticated, logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar position="static">
        <Toolbar>
          <Box sx={{ flexGrow: 1 }} />
          {isAuthenticated && user ? (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Typography variant="body1">
                {user.email}
              </Typography>
              <Button
                color="inherit"
                component={RouterLink}
                to="/dashboard"
              >
                {t('common.dashboard')}
              </Button>
              <Button
                color="inherit"
                startIcon={<Logout />}
                onClick={handleLogout}
              >
                {t('auth.logout')}
              </Button>
            </Box>
          ) : (
            <Button
              color="inherit"
              component={RouterLink}
              to="/login"
            >
              {t('auth.login')}
            </Button>
          )}
        </Toolbar>
      </AppBar>

      <Container component="main" sx={{ mt: 8, mb: 4, flex: 1 }}>
        <Typography
          variant="h2"
          component="h1"
          align="center"
          sx={{ mt: 8 }}
        >
          {t('home.workingOnCreation')}
        </Typography>
      </Container>
    </Box>
  );
} 