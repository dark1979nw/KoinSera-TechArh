import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Paper,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  DataGrid,
  GridColDef,
  GridToolbar,
} from '@mui/x-data-grid';
import { api } from '../../contexts/AuthContext';
import { Lock, AdminPanelSettings, PersonOff, Person } from '@mui/icons-material';

interface User {
  id: number;
  login: string;
  email: string;
  first_name: string;
  last_name: string;
  company: string | null;
  language_code: string;
  is_admin: boolean;
  is_active: boolean;
  created_at: string;
  last_login: string | null;
}

interface UserUpdate {
  is_admin?: boolean;
  is_active?: boolean;
  password?: string;
}

export default function AdminPanel() {
  const { t } = useTranslation();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [newPassword, setNewPassword] = useState('');
  const [openPasswordDialog, setOpenPasswordDialog] = useState(false);

  const fetchUsers = async () => {
    try {
      const token = localStorage.getItem('token');
      console.log('Current token:', token);
      
      console.log('Fetching users...');
      const response = await api.get('/api/admin/users', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      console.log('Users response:', response.data);
      console.log('First user data:', response.data[0]);
      setUsers(response.data);
    } catch (error: any) {
      console.error('Error fetching users:', error);
      console.error('Error details:', {
        status: error.response?.status,
        data: error.response?.data,
        headers: error.config?.headers
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleUpdateUser = async (userId: number, updates: UserUpdate) => {
    try {
      await api.put(`/api/admin/users/${userId}`, updates);
      await fetchUsers(); // Обновляем список пользователей
    } catch (error) {
      console.error('Error updating user:', error);
    }
  };

  const handlePasswordChange = async () => {
    if (selectedUser && newPassword) {
      await handleUpdateUser(selectedUser.id, { password: newPassword });
      setOpenPasswordDialog(false);
      setNewPassword('');
      setSelectedUser(null);
    }
  };

  const columns: GridColDef[] = [
    { field: 'id', headerName: 'ID', width: 70 },
    { field: 'login', headerName: t('admin.users.login'), width: 130 },
    { field: 'email', headerName: t('admin.users.email'), width: 200 },
    { field: 'first_name', headerName: t('admin.users.firstName'), width: 130 },
    { field: 'last_name', headerName: t('admin.users.lastName'), width: 130 },
    { 
      field: 'company',
      headerName: t('admin.users.company'),
      width: 150,
      renderCell: (params) => {
        return params.row.company || '-';
      }
    },
    { field: 'language_code', headerName: t('admin.users.language'), width: 100 },
    {
      field: 'is_active',
      headerName: t('admin.users.isActive'),
      width: 100,
      renderCell: (params) => (
        <Box
          sx={{
            color: params.row.is_active ? 'success.main' : 'error.main',
            fontWeight: 'bold'
          }}
        >
          {params.row.is_active ? t('common.yes') : t('common.no')}
        </Box>
      )
    },
    {
      field: 'is_admin',
      headerName: t('admin.users.isAdmin'),
      width: 100,
      renderCell: (params) => (
        <Box
          sx={{
            color: params.row.is_admin ? 'success.main' : 'error.main',
            fontWeight: 'bold'
          }}
        >
          {params.row.is_admin ? t('common.yes') : t('common.no')}
        </Box>
      )
    },
    {
      field: 'actions',
      headerName: t('admin.users.actions'),
      width: 200,
      renderCell: (params) => (
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title={t('admin.users.changePassword')}>
            <IconButton
              size="small"
              onClick={() => {
                setSelectedUser(params.row);
                setOpenPasswordDialog(true);
              }}
            >
              <Lock />
            </IconButton>
          </Tooltip>
          <Tooltip title={params.row.is_admin ? t('admin.users.removeAdmin') : t('admin.users.makeAdmin')}>
            <IconButton
              size="small"
              onClick={() => handleUpdateUser(params.row.id, { is_admin: !params.row.is_admin })}
            >
              <AdminPanelSettings color={params.row.is_admin ? 'primary' : 'action'} />
            </IconButton>
          </Tooltip>
          <Tooltip title={params.row.is_active ? t('admin.users.deactivate') : t('admin.users.activate')}>
            <IconButton
              size="small"
              onClick={() => handleUpdateUser(params.row.id, { is_active: !params.row.is_active })}
            >
              {params.row.is_active ? <PersonOff /> : <Person />}
            </IconButton>
          </Tooltip>
        </Box>
      )
    },
    {
      field: 'created_at',
      headerName: t('admin.users.createdAt'),
      width: 180,
      renderCell: (params) => {
        const dateStr = params.row.created_at;
        if (!dateStr) return '-';
        
        try {
          const date = new Date(dateStr);
          if (isNaN(date.getTime())) return '-';
          
          const year = date.getFullYear();
          const month = String(date.getMonth() + 1).padStart(2, '0');
          const day = String(date.getDate()).padStart(2, '0');
          const hours = String(date.getHours()).padStart(2, '0');
          const minutes = String(date.getMinutes()).padStart(2, '0');
          const seconds = String(date.getSeconds()).padStart(2, '0');
          
          return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
        } catch (e) {
          console.error('Error formatting date:', e);
          return '-';
        }
      }
    },
    {
      field: 'last_login',
      headerName: t('admin.users.lastLogin'),
      width: 180,
      renderCell: (params) => {
        const dateStr = params.row.last_login;
        if (!dateStr) return '-';
        
        try {
          const date = new Date(dateStr);
          if (isNaN(date.getTime())) return '-';
          
          const year = date.getFullYear();
          const month = String(date.getMonth() + 1).padStart(2, '0');
          const day = String(date.getDate()).padStart(2, '0');
          const hours = String(date.getHours()).padStart(2, '0');
          const minutes = String(date.getMinutes()).padStart(2, '0');
          const seconds = String(date.getSeconds()).padStart(2, '0');
          
          return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
        } catch (e) {
          console.error('Error formatting date:', e);
          return '-';
        }
      }
    },
  ];

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        {t('admin.title')}
      </Typography>
      <Paper sx={{ height: 'calc(100vh - 200px)', width: '100%' }}>
        <DataGrid
          rows={users}
          columns={columns}
          initialState={{
            pagination: {
              paginationModel: { page: 0, pageSize: 10 },
            },
            sorting: {
              sortModel: [{ field: 'id', sort: 'desc' }],
            },
          }}
          pageSizeOptions={[10, 25, 50]}
          loading={loading}
          slots={{ toolbar: GridToolbar }}
          slotProps={{
            toolbar: {
              showQuickFilter: true,
              quickFilterProps: { debounceMs: 500 },
            },
          }}
          disableRowSelectionOnClick
        />
      </Paper>

      {/* Диалог изменения пароля */}
      <Dialog open={openPasswordDialog} onClose={() => setOpenPasswordDialog(false)}>
        <DialogTitle>{t('admin.users.changePassword')}</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label={t('auth.password')}
            type="password"
            fullWidth
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenPasswordDialog(false)}>
            {t('common.cancel')}
          </Button>
          <Button onClick={handlePasswordChange} color="primary">
            {t('common.save')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
} 