import { useAuth } from '../hooks/useAuth';
import { useTranslation } from 'react-i18next';
import {
  Container,
  Box,
  Typography,
  Button,
  Paper,
} from '@mui/material';

export default function Dashboard() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();

  return (
    <Container component="main" maxWidth="md">
      <Box
        sx={{
          marginTop: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Paper
          elevation={3}
          sx={{
            padding: 4,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            width: '100%',
          }}
        >
          <Typography component="h1" variant="h4" gutterBottom>
            {t('dashboard.welcome')}
          </Typography>
          
          <Box sx={{ mt: 2, textAlign: 'center' }}>
            <Typography variant="body1" gutterBottom>
              {t('dashboard.loggedInAs')}: {user?.email}
            </Typography>
            <Typography variant="body1" gutterBottom>
              {t('dashboard.name')}: {user?.first_name} {user?.last_name}
            </Typography>
            {user?.company && (
              <Typography variant="body1" gutterBottom>
                {t('dashboard.company')}: {user.company}
              </Typography>
            )}
          </Box>

          <Button
            variant="contained"
            color="primary"
            onClick={logout}
            sx={{ mt: 3 }}
          >
            {t('auth.logout')}
          </Button>
        </Paper>
      </Box>
    </Container>
  );
} 