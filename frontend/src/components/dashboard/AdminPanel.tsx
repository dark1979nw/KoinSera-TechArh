import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Paper,
  Typography,
} from '@mui/material';
import {
  DataGrid,
  GridColDef,
  GridRenderCellParams,
  GridToolbar,
} from '@mui/x-data-grid';
import { api } from '../../contexts/AuthContext';

interface User {
  id: number;
  login: string;
  email: string;
  first_name: string;
  last_name: string;
  company: string | null;
  language_code: string;
  is_admin: boolean;
  created_at: string;
  last_login: string | null;
}

export default function AdminPanel() {
  const { t } = useTranslation();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
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

    fetchUsers();
  }, []);

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
      valueGetter: (params: GridRenderCellParams) => {
        return params?.row?.company || '-';
      },
    },
    { field: 'language_code', headerName: t('admin.users.language'), width: 100 },
    {
      field: 'is_admin',
      headerName: t('admin.users.isAdmin'),
      width: 100,
      type: 'boolean',
    },
    {
      field: 'created_at',
      headerName: t('admin.users.createdAt'),
      width: 180,
      valueGetter: (params: GridRenderCellParams) => {
        return params?.row?.created_at ? new Date(params.row.created_at).toLocaleString() : '-';
      },
    },
    {
      field: 'last_login',
      headerName: t('admin.users.lastLogin'),
      width: 180,
      valueGetter: (params: GridRenderCellParams) => {
        return params?.row?.last_login ? new Date(params.row.last_login).toLocaleString() : '-';
      },
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
    </Box>
  );
} 