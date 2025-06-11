import { useState } from 'react';
import { useNavigate, Link as RouterLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Container,
  Box,
  Typography,
  TextField,
  Button,
  Link,
  Paper,
  Alert,
  Grid,
} from '@mui/material';
import { useAuth } from '../contexts/AuthContext.tsx';

interface RegisterFormData {
  login: string;
  email: string;
  password: string;
  confirmPassword: string;
  firstName: string;
  lastName: string;
  company?: string;
}

interface FormErrors {
  login?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
  firstName?: string;
  lastName?: string;
  company?: string;
}

export default function Register() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { register } = useAuth();
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [formErrors, setFormErrors] = useState<FormErrors>({});
  const [formData, setFormData] = useState<RegisterFormData>({
    login: '',
    email: '',
    password: '',
    confirmPassword: '',
    firstName: '',
    lastName: '',
    company: '',
  });

  const validateForm = (): boolean => {
    const errors: FormErrors = {};
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const loginRegex = /^[a-zA-Z0-9]+$/;
    const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?])[A-Za-z\d!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]{8,}$/;

    // Login validation
    if (!formData.login.trim()) {
      errors.login = t('validation.required', { field: t('auth.login') });
    } else if (formData.login.length < 3 || formData.login.length > 50) {
      errors.login = t('validation.loginLength');
    } else if (!loginRegex.test(formData.login)) {
      errors.login = t('validation.loginAlphanumeric');
    }

    // Email validation
    if (!formData.email.trim()) {
      errors.email = t('validation.required', { field: t('auth.email') });
    } else if (!emailRegex.test(formData.email)) {
      errors.email = t('validation.email');
    }

    // Password validation
    if (!formData.password) {
      errors.password = t('validation.required', { field: t('auth.password') });
    } else if (!passwordRegex.test(formData.password)) {
      errors.password = t('validation.passwordRequirements');
    }

    // Confirm password validation
    if (!formData.confirmPassword) {
      errors.confirmPassword = t('validation.required', { field: t('auth.confirmPassword') });
    } else if (formData.password !== formData.confirmPassword) {
      errors.confirmPassword = t('validation.passwordMatch');
    }

    // First name validation
    if (!formData.firstName.trim()) {
      errors.firstName = t('validation.required', { field: t('auth.firstName') });
    } else if (formData.firstName.length > 50) {
      errors.firstName = t('validation.nameLength');
    }

    // Last name validation
    if (!formData.lastName.trim()) {
      errors.lastName = t('validation.required', { field: t('auth.lastName') });
    } else if (formData.lastName.length > 50) {
      errors.lastName = t('validation.nameLength');
    }

    // Company validation (optional)
    if (formData.company && formData.company.length > 100) {
      errors.company = t('validation.companyLength');
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setFormErrors({});

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      await register({
        login: formData.login.trim(),
        email: formData.email.trim(),
        password: formData.password,
        first_name: formData.firstName.trim(),
        last_name: formData.lastName.trim(),
        company: formData.company?.trim() || undefined,
      });
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || t('auth.registerError'));
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // Clear error when user starts typing
    if (formErrors[name as keyof FormErrors]) {
      setFormErrors(prev => ({ ...prev, [name]: undefined }));
    }
  };

  return (
    <Container component="main" maxWidth="sm">
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
          <Typography component="h1" variant="h5">
            {t('auth.register')}
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mt: 2, width: '100%' }}>
              {error}
            </Alert>
          )}

          <Box component="form" onSubmit={handleSubmit} sx={{ mt: 3, width: '100%' }}>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  required
                  fullWidth
                  id="firstName"
                  label={t('auth.firstName')}
                  name="firstName"
                  autoComplete="given-name"
                  value={formData.firstName}
                  onChange={handleChange}
                  error={!!formErrors.firstName}
                  helperText={formErrors.firstName}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  required
                  fullWidth
                  id="lastName"
                  label={t('auth.lastName')}
                  name="lastName"
                  autoComplete="family-name"
                  value={formData.lastName}
                  onChange={handleChange}
                  error={!!formErrors.lastName}
                  helperText={formErrors.lastName}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  required
                  fullWidth
                  id="login"
                  label={t('auth.login')}
                  name="login"
                  autoComplete="username"
                  value={formData.login}
                  onChange={handleChange}
                  error={!!formErrors.login}
                  helperText={formErrors.login}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  required
                  fullWidth
                  id="email"
                  label={t('auth.email')}
                  name="email"
                  type="email"
                  autoComplete="email"
                  value={formData.email}
                  onChange={handleChange}
                  error={!!formErrors.email}
                  helperText={formErrors.email}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  id="company"
                  label={t('auth.company')}
                  name="company"
                  value={formData.company}
                  onChange={handleChange}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  required
                  fullWidth
                  name="password"
                  label={t('auth.password')}
                  type="password"
                  id="password"
                  autoComplete="new-password"
                  value={formData.password}
                  onChange={handleChange}
                  error={!!formErrors.password}
                  helperText={formErrors.password}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  required
                  fullWidth
                  name="confirmPassword"
                  label={t('auth.confirmPassword')}
                  type="password"
                  id="confirmPassword"
                  autoComplete="new-password"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  error={!!formErrors.confirmPassword}
                  helperText={formErrors.confirmPassword}
                />
              </Grid>
            </Grid>
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
              disabled={loading}
            >
              {loading ? t('common.loading') : t('auth.signUp')}
            </Button>
            <Box sx={{ textAlign: 'center' }}>
              <Link component={RouterLink} to="/login" variant="body2">
                {t('auth.hasAccount')}
              </Link>
            </Box>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
} 