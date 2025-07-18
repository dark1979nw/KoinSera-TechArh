import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Box, Typography, Paper, Button } from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { api } from '../../contexts/AuthContext';
import { Delete } from '@mui/icons-material';
import { IconButton, Switch } from '@mui/material';

interface Participant {
  employee_id: number;
  full_name: string;
  telegram_username: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  is_external: boolean;
  is_admin: boolean;
  ce_is_active: boolean;
  ce_updated_at: string;
}

export default function Participants() {
  const { chatId } = useParams<{ chatId: string }>();
  const navigate = useNavigate();
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [chatTitle, setChatTitle] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!chatId) return;
    api.get(`/api/chats/${chatId}/participants`).then(res => {
      setParticipants(res.data.participants);
      setChatTitle(res.data.chat_title || '');
    }).finally(() => setLoading(false));
  }, [chatId]);

  const handleDelete = async (employee_id: number) => {
    if (!chatId) return;
    if (!window.confirm('Удалить связь с этим участником?')) return;
    await api.delete(`/api/chats/${chatId}/participants/${employee_id}`);
    setParticipants(participants.filter(p => p.employee_id !== employee_id));
  };

  const handleSwitch = async (employee_id: number, field: string, value: boolean) => {
    if (!chatId) return;
    await api.put(`/api/chats/${chatId}/participants/${employee_id}`, { [field]: value });
    setParticipants(participants => participants.map(p => p.employee_id === employee_id ? { ...p, [field]: value } : p));
  };

  const columns: GridColDef[] = [
    { field: 'employee_id', headerName: 'ID', width: 70 },
    { field: 'full_name', headerName: 'Full Name', width: 200 },
    { field: 'telegram_username', headerName: 'Telegram Username', width: 180 },
    { field: 'created_at', headerName: 'Created At', width: 180 },
    { field: 'updated_at', headerName: 'Updated At', width: 180 },
    {
      field: 'is_active',
      headerName: 'Active',
      width: 100,
      renderCell: (params) => (
        <Switch
          checked={!!params.value}
          onChange={e => handleSwitch(params.row.employee_id, 'is_active', e.target.checked)}
          color="primary"
        />
      ),
    },
    {
      field: 'is_external',
      headerName: 'External',
      width: 100,
      renderCell: (params) => (
        <Switch
          checked={!!params.value}
          onChange={e => handleSwitch(params.row.employee_id, 'is_external', e.target.checked)}
          color="primary"
        />
      ),
    },
    {
      field: 'is_admin',
      headerName: 'Admin',
      width: 100,
      renderCell: (params) => (
        <Switch
          checked={!!params.value}
          onChange={e => handleSwitch(params.row.employee_id, 'is_admin', e.target.checked)}
          color="primary"
        />
      ),
    },
    {
      field: 'ce_is_active',
      headerName: 'Link Active',
      width: 120,
      renderCell: (params) => (
        <Switch
          checked={!!params.value}
          onChange={e => handleSwitch(params.row.employee_id, 'ce_is_active', e.target.checked)}
          color="primary"
        />
      ),
    },
    { field: 'ce_updated_at', headerName: 'Link Updated', width: 180 },
    {
      field: 'actions',
      headerName: '',
      width: 80,
      renderCell: (params) => (
        <IconButton color="error" onClick={() => handleDelete(params.row.employee_id)}>
          <Delete />
        </IconButton>
      ),
      sortable: false,
      filterable: false,
      disableColumnMenu: true,
    },
  ];

  return (
    <Box sx={{ p: 3 }}>
      <Button variant="outlined" onClick={() => navigate(-1)} sx={{ mb: 2 }}>Back</Button>
      <Typography variant="h4" gutterBottom>
        {chatTitle ? `Участники чата: ${chatTitle}` : 'Участники чата'}
      </Typography>
      <Paper sx={{ height: 'calc(100vh - 200px)', width: '100%' }}>
        <DataGrid
          rows={participants}
          columns={columns}
          getRowId={row => row.employee_id}
          loading={loading}
          pageSizeOptions={[10, 25, 50]}
          initialState={{
            pagination: { paginationModel: { page: 0, pageSize: 10 } },
            sorting: { sortModel: [{ field: 'employee_id', sort: 'asc' }] },
          }}
        />
      </Paper>
    </Box>
  );
} 