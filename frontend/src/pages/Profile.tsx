import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Box, Paper, Typography, TextField, Button, MenuItem } from '@mui/material';
import { api } from '../contexts/AuthContext';

interface UserProfile {
  user_id: number;
  login: string;
  email: string;
  first_name: string;
  last_name: string;
  company?: string;
  language_code: string;
}

export default function Profile() {
  const { t } = useTranslation();
  const [, setProfile] = useState<UserProfile | null>(null);
  const [editProfile, setEditProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [password, setPassword] = useState('');
  const [password2, setPassword2] = useState('');

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/auth/me');
      setProfile(response.data);
      setEditProfile(response.data);
    } catch (e) {
      setError('Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!editProfile) return;
    setSaving(true);
    setError(null);
    if (password) {
      if (password.length < 8 || !/[A-Za-z]/.test(password) || !/\d/.test(password)) {
        setError(t('validation.passwordRequirements') || 'Password must be at least 8 characters and contain both letters and numbers.');
        setSaving(false);
        return;
      }
      if (password !== password2) {
        setError(t('validation.passwordMatch') || 'Passwords do not match');
        setSaving(false);
        return;
      }
    }
    try {
      await api.put(`/api/admin/me`, {
        first_name: editProfile.first_name,
        last_name: editProfile.last_name,
        email: editProfile.email,
        company: editProfile.company,
        language_code: editProfile.language_code,
        ...(password ? { password } : {}),
      });
      setProfile(editProfile);
      setPassword('');
      setPassword2('');
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to save profile');
    } finally {
      setSaving(false);
    }
  };

  if (loading || !editProfile) return <Typography>{t('common.loading')}</Typography>;

  return (
    <Box sx={{ p: 3, maxWidth: 500, margin: '0 auto' }}>
      <Typography variant="h4" gutterBottom>{t('dashboard.profile') || 'Profile'}</Typography>
      <Paper sx={{ p: 3 }}>
        <TextField
          label={t('auth.login') || 'Login'}
          value={editProfile.login}
          fullWidth
          margin="normal"
          disabled
        />
        <TextField
          label={t('auth.email') || 'Email'}
          value={editProfile.email}
          onChange={e => setEditProfile({ ...editProfile, email: e.target.value })}
          fullWidth
          margin="normal"
        />
        <TextField
          label={t('auth.firstName') || 'First Name'}
          value={editProfile.first_name}
          onChange={e => setEditProfile({ ...editProfile, first_name: e.target.value })}
          fullWidth
          margin="normal"
        />
        <TextField
          label={t('auth.lastName') || 'Last Name'}
          value={editProfile.last_name}
          onChange={e => setEditProfile({ ...editProfile, last_name: e.target.value })}
          fullWidth
          margin="normal"
        />
        <TextField
          label={t('auth.company') || 'Company'}
          value={editProfile.company || ''}
          onChange={e => setEditProfile({ ...editProfile, company: e.target.value })}
          fullWidth
          margin="normal"
        />
        <TextField
          select
          label={t('admin.users.language') || 'Language'}
          value={editProfile.language_code}
          onChange={e => setEditProfile({ ...editProfile, language_code: e.target.value })}
          fullWidth
          margin="normal"
        >
          <MenuItem value="en">English</MenuItem>
          <MenuItem value="ru">Русский</MenuItem>
        </TextField>
        <TextField
          label={t('auth.password') || 'New Password'}
          type="password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          fullWidth
          margin="normal"
          autoComplete="new-password"
        />
        <TextField
          label={t('auth.confirmPassword') || 'Confirm Password'}
          type="password"
          value={password2}
          onChange={e => setPassword2(e.target.value)}
          fullWidth
          margin="normal"
          autoComplete="new-password"
        />
        {error && <Typography color="error">{error}</Typography>}
        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
          <Button variant="contained" color="primary" onClick={handleSave} disabled={saving}>
            {t('common.save') || 'Save'}
          </Button>
        </Box>
      </Paper>
    </Box>
  );
} 