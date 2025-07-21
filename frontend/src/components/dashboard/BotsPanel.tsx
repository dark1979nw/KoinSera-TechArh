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
import { Add, Edit, Delete, PowerSettingsNew } from '@mui/icons-material';

interface Bot {
  bot_id: number;
  user_id: number;
  bot_name: string;
  bot_token: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

interface BotCreate {
  bot_name: string;
  bot_token: string;
  is_active: boolean;
}

export default function BotsPanel() {
  const { t } = useTranslation();
  const [bots, setBots] = useState<Bot[]>([]);
  const [loading, setLoading] = useState(true);
  const [openDialog, setOpenDialog] = useState(false);
  const [selectedBot, setSelectedBot] = useState<Bot | null>(null);
  const [newBot, setNewBot] = useState<BotCreate>({
    bot_name: '',
    bot_token: '',
    is_active: true
  });

  useEffect(() => {
    fetchBots();
  }, []);

  const fetchBots = async () => {
    try {
      const response = await api.get('/api/bots');
      setBots(response.data);
    } catch (error) {
      console.error('Error fetching bots:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateBot = async () => {
    try {
      await api.post('/api/bots', newBot);
      setOpenDialog(false);
      setNewBot({ bot_name: '', bot_token: '', is_active: true });
      await fetchBots();
    } catch (error) {
      console.error('Error creating bot:', error);
    }
  };

  const handleUpdateBot = async (botId: number, updates: Partial<Bot>) => {
    try {
      await api.put(`/api/bots/${botId}`, updates);
      await fetchBots();
    } catch (error) {
      console.error('Error updating bot:', error);
    }
  };

  const handleDeleteBot = async (botId: number) => {
    if (window.confirm(t('bots.confirmDelete'))) {
      try {
        await api.delete(`/api/bots/${botId}`);
        await fetchBots();
      } catch (error) {
        console.error('Error deleting bot:', error);
      }
    }
  };

  const columns: GridColDef[] = [
    { field: 'bot_id', headerName: 'ID', width: 70 },
    { field: 'bot_name', headerName: t('bots.name'), width: 200 },
    { field: 'bot_token', headerName: t('bots.token'), width: 300 },
    {
      field: 'is_active',
      headerName: t('bots.isActive'),
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
      field: 'created_at',
      headerName: t('bots.createdAt'),
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
      field: 'actions',
      headerName: t('bots.actions'),
      width: 200,
      renderCell: (params) => (
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title={params.row.is_active ? t('bots.deactivate') : t('bots.activate')}>
            <IconButton
              size="small"
              onClick={() => handleUpdateBot(params.row.bot_id, { is_active: !params.row.is_active })}
            >
              <PowerSettingsNew color={params.row.is_active ? 'success' : 'error'} />
            </IconButton>
          </Tooltip>
          <Tooltip title={t('bots.edit')}>
            <IconButton
              size="small"
              onClick={() => {
                setSelectedBot(params.row);
                setOpenDialog(true);
              }}
            >
              <Edit />
            </IconButton>
          </Tooltip>
          <Tooltip title={t('bots.delete')}>
            <IconButton
              size="small"
              onClick={() => handleDeleteBot(params.row.bot_id)}
            >
              <Delete />
            </IconButton>
          </Tooltip>
        </Box>
      )
    },
  ];

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h4">
          {t('bots.title')}
        </Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => {
            setSelectedBot(null);
            setOpenDialog(true);
          }}
        >
          {t('bots.addNew')}
        </Button>
      </Box>
      <Paper sx={{ height: 'calc(100vh - 200px)', width: '100%' }}>
        <DataGrid
          rows={bots}
          columns={columns}
          getRowId={(row) => row.bot_id}
          initialState={{
            pagination: {
              paginationModel: { page: 0, pageSize: 10 },
            },
            sorting: {
              sortModel: [{ field: 'bot_id', sort: 'desc' }],
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
        <DialogTitle>
          {selectedBot ? t('bots.editBot') : t('bots.addNew')}
        </DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label={t('bots.name')}
            fullWidth
            value={selectedBot ? selectedBot.bot_name : newBot.bot_name}
            onChange={(e) => {
              if (selectedBot) {
                setSelectedBot({ ...selectedBot, bot_name: e.target.value });
              } else {
                setNewBot({ ...newBot, bot_name: e.target.value });
              }
            }}
          />
          <TextField
            margin="dense"
            label={t('bots.token')}
            fullWidth
            value={selectedBot ? selectedBot.bot_token : newBot.bot_token}
            onChange={(e) => {
              if (selectedBot) {
                setSelectedBot({ ...selectedBot, bot_token: e.target.value });
              } else {
                setNewBot({ ...newBot, bot_token: e.target.value });
              }
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>
            {t('common.cancel')}
          </Button>
          <Button
            onClick={() => {
              if (selectedBot) {
                handleUpdateBot(selectedBot.bot_id, {
                  bot_name: selectedBot.bot_name,
                  bot_token: selectedBot.bot_token
                });
                setOpenDialog(false);
                setSelectedBot(null);
              } else {
                handleCreateBot();
              }
            }}
            color="primary"
          >
            {t('common.save')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
} 