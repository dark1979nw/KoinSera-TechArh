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
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  DataGrid,
  GridColDef,
  GridToolbar,
} from '@mui/x-data-grid';
import { api } from '../../contexts/AuthContext';
import { Edit, Delete } from '@mui/icons-material';

interface Employee {
  employee_id: number;
  full_name: string;
  telegram_username?: string;
  telegram_user_id?: number;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  is_external: boolean;
  user_id?: number;
  is_bot: boolean;
}

interface EmployeeCreate {
  full_name: string;
  telegram_username?: string;
  telegram_user_id?: number;
  is_active?: boolean;
  is_external?: boolean;
  is_bot?: boolean;
}

export default function UsersPanel() {
  const { t } = useTranslation();
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);
  const [openDialog, setOpenDialog] = useState(false);
  const [newEmployee, setNewEmployee] = useState<EmployeeCreate>({
    full_name: '',
    telegram_username: '',
    telegram_user_id: undefined,
    is_active: true,
    is_external: true,
    is_bot: false,
  });
  const [selectedEmployee, setSelectedEmployee] = useState<Employee | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editEmployee, setEditEmployee] = useState<EmployeeCreate | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchEmployees();
  }, []);

  const fetchEmployees = async () => {
    try {
      const response = await api.get('/api/employees');
      setEmployees(response.data);
    } catch (error) {
      console.error('Error fetching employees:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateEmployee = async () => {
    try {
      await api.post('/api/employees', newEmployee);
      setOpenDialog(false);
      setNewEmployee({
        full_name: '',
        telegram_username: '',
        telegram_user_id: undefined,
        is_active: true,
        is_external: true,
        is_bot: false,
      });
      await fetchEmployees();
    } catch (error) {
      console.error('Error creating employee:', error);
    }
  };

  const handleDeleteEmployee = async (employeeId: number) => {
    if (!window.confirm(t('users.confirmDelete') || 'Delete this user?')) return;
    try {
      await api.delete(`/api/employees/${employeeId}`);
      await fetchEmployees();
    } catch (error) {
      console.error('Error deleting employee:', error);
    }
  };

  const handleEditEmployee = (employee: Employee) => {
    setEditEmployee({
      full_name: employee.full_name,
      telegram_username: employee.telegram_username,
      telegram_user_id: employee.telegram_user_id,
      is_active: employee.is_active,
      is_external: employee.is_external,
      is_bot: employee.is_bot,
    });
    setSelectedEmployee(employee);
    setEditDialogOpen(true);
    setError(null);
  };

  const handleSaveEditEmployee = async () => {
    if (!editEmployee || !selectedEmployee) return;
    if (!editEmployee.full_name) {
      setError(t('users.validation.fullNameRequired') || 'Full Name is required');
      return;
    }
    try {
      await api.put(`/api/employees/${selectedEmployee.employee_id}`, editEmployee);
      setEditDialogOpen(false);
      setSelectedEmployee(null);
      setEditEmployee(null);
      await fetchEmployees();
    } catch (error) {
      console.error('Error updating employee:', error);
    }
  };

  const columns: GridColDef[] = [
    { field: 'employee_id', headerName: 'ID', width: 70 },
    { field: 'full_name', headerName: t('users.fullName') || 'Full Name', width: 200 },
    { field: 'telegram_username', headerName: t('users.telegramUsername') || 'Telegram Username', width: 180 },
    { field: 'telegram_user_id', headerName: t('users.telegramUserId') || 'Telegram User ID', width: 180 },
    {
      field: 'is_active',
      headerName: t('users.isActive') || 'Active',
      width: 100,
      renderCell: (params) => params.row.is_active ? t('common.yes') : t('common.no'),
    },
    {
      field: 'is_external',
      headerName: t('users.isExternal') || 'External',
      width: 100,
      renderCell: (params) => params.row.is_external ? t('common.yes') : t('common.no'),
    },
    {
      field: 'is_bot',
      headerName: t('users.isBot') || 'Bot',
      width: 100,
      renderCell: (params) => params.row.is_bot ? t('common.yes') : t('common.no'),
    },
    {
      field: 'created_at',
      headerName: t('users.createdAt') || 'Created At',
      width: 180,
      renderCell: (params) => {
        const dateStr = params.row.created_at;
        if (!dateStr) return '-';
        try {
          const date = new Date(dateStr);
          if (isNaN(date.getTime())) return '-';
          return date.toLocaleString();
        } catch (e) {
          return '-';
        }
      }
    },
    {
      field: 'updated_at',
      headerName: t('users.updatedAt') || 'Updated At',
      width: 180,
      renderCell: (params) => {
        const dateStr = params.row.updated_at;
        if (!dateStr) return '-';
        try {
          const date = new Date(dateStr);
          if (isNaN(date.getTime())) return '-';
          return date.toLocaleString();
        } catch (e) {
          return '-';
        }
      }
    },
    {
      field: 'actions',
      headerName: t('users.actions') || 'Actions',
      width: 150,
      renderCell: (params) => (
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button size="small" onClick={() => handleEditEmployee(params.row)}><Edit fontSize="small" /></Button>
          <Button size="small" color="error" onClick={() => handleDeleteEmployee(params.row.employee_id)}><Delete fontSize="small" /></Button>
        </Box>
      )
    },
  ];

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h4">
          {t('users.title') || 'Users'}
        </Typography>
        <Button
          variant="contained"
          onClick={() => setOpenDialog(true)}
        >
          {t('users.addNew') || 'Add New'}
        </Button>
      </Box>
      <Paper sx={{ height: 'calc(100vh - 200px)', width: '100%' }}>
        <DataGrid
          rows={employees}
          columns={columns}
          getRowId={(row) => row.employee_id}
          initialState={{
            pagination: {
              paginationModel: { page: 0, pageSize: 10 },
            },
            sorting: {
              sortModel: [{ field: 'employee_id', sort: 'desc' }],
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
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)}>
        <DialogTitle>{t('users.addNew') || 'Add New User'}</DialogTitle>
        <DialogContent>
          {error && <Typography color="error">{error}</Typography>}
          <TextField
            autoFocus
            margin="dense"
            label={t('users.fullName') || 'Full Name'}
            type="text"
            fullWidth
            value={newEmployee.full_name}
            onChange={(e) => setNewEmployee({ ...newEmployee, full_name: e.target.value })}
            error={!newEmployee.full_name}
            helperText={!newEmployee.full_name ? (t('users.validation.fullNameRequired') || 'Full Name is required') : ''}
          />
          <TextField
            margin="dense"
            label={t('users.telegramUsername') || 'Telegram Username'}
            type="text"
            fullWidth
            value={newEmployee.telegram_username}
            onChange={(e) => setNewEmployee({ ...newEmployee, telegram_username: e.target.value })}
          />
          <TextField
            margin="dense"
            label={t('users.telegramUserId') || 'Telegram User ID'}
            type="number"
            fullWidth
            value={newEmployee.telegram_user_id || ''}
            onChange={(e) => setNewEmployee({ ...newEmployee, telegram_user_id: e.target.value ? Number(e.target.value) : undefined })}
          />
          <FormControlLabel
            control={<Switch checked={!!newEmployee.is_active} onChange={e => setNewEmployee({ ...newEmployee, is_active: e.target.checked })} />}
            label={t('users.isActive') || 'Active'}
          />
          <FormControlLabel
            control={<Switch checked={!!newEmployee.is_external} onChange={e => setNewEmployee({ ...newEmployee, is_external: e.target.checked })} />}
            label={t('users.isExternal') || 'External'}
          />
          <FormControlLabel
            control={<Switch checked={!!newEmployee.is_bot} onChange={e => setNewEmployee({ ...newEmployee, is_bot: e.target.checked })} />}
            label={t('users.isBot') || 'Bot'}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>{t('common.cancel') || 'Cancel'}</Button>
          <Button onClick={handleCreateEmployee} color="primary" disabled={!newEmployee.full_name}>
            {t('common.save') || 'Save'}
          </Button>
        </DialogActions>
      </Dialog>
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)}>
        <DialogTitle>{t('users.editUser') || 'Edit User'}</DialogTitle>
        <DialogContent>
          {error && <Typography color="error">{error}</Typography>}
          <TextField
            autoFocus
            margin="dense"
            label={t('users.fullName') || 'Full Name'}
            type="text"
            fullWidth
            value={editEmployee?.full_name || ''}
            onChange={(e) => setEditEmployee({ ...editEmployee!, full_name: e.target.value })}
            error={!editEmployee?.full_name}
            helperText={!editEmployee?.full_name ? (t('users.validation.fullNameRequired') || 'Full Name is required') : ''}
          />
          <TextField
            margin="dense"
            label={t('users.telegramUsername') || 'Telegram Username'}
            type="text"
            fullWidth
            value={editEmployee?.telegram_username || ''}
            onChange={(e) => setEditEmployee({ ...editEmployee!, telegram_username: e.target.value })}
          />
          <TextField
            margin="dense"
            label={t('users.telegramUserId') || 'Telegram User ID'}
            type="number"
            fullWidth
            value={editEmployee?.telegram_user_id || ''}
            onChange={(e) => setEditEmployee({ ...editEmployee!, telegram_user_id: e.target.value ? Number(e.target.value) : undefined })}
          />
          <FormControlLabel
            control={<Switch checked={!!editEmployee?.is_active} onChange={e => setEditEmployee({ ...editEmployee!, is_active: e.target.checked })} />}
            label={t('users.isActive') || 'Active'}
          />
          <FormControlLabel
            control={<Switch checked={!!editEmployee?.is_external} onChange={e => setEditEmployee({ ...editEmployee!, is_external: e.target.checked })} />}
            label={t('users.isExternal') || 'External'}
          />
          <FormControlLabel
            control={<Switch checked={!!editEmployee?.is_bot} onChange={e => setEditEmployee({ ...editEmployee!, is_bot: e.target.checked })} />}
            label={t('users.isBot') || 'Bot'}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>{t('common.cancel') || 'Cancel'}</Button>
          <Button onClick={handleSaveEditEmployee} color="primary" disabled={!editEmployee?.full_name}>
            {t('common.save') || 'Save'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
} 