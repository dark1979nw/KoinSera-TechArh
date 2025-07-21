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
  MenuItem,
  Select,
  InputLabel,
  FormControl,
} from '@mui/material';
import {
  DataGrid,
  GridColDef,
  GridToolbar,
} from '@mui/x-data-grid';
import { api } from '../../contexts/AuthContext';
import { Delete } from '@mui/icons-material';
import './ChatsPanel.css';
import { useNavigate } from 'react-router-dom';

interface Chat {
  chat_id: number;
  bot_id: number;
  user_id: number;
  telegram_chat_id: string;
  title: string | null;
  type_id: number;
  status_id: number;
  user_num: number;
  unknown_user: number;
  created_at: string;
  updated_at: string;
}

export default function ChatsPanel() {
  const { t } = useTranslation();
  const [chats, setChats] = useState<Chat[]>([]);
  const [loading, setLoading] = useState(true);
  const [chatTypes, setChatTypes] = useState<{ [key: number]: string }>({});
  const [chatStatuses, setChatStatuses] = useState<{ [key: number]: string }>({});
  const [openDialog, setOpenDialog] = useState(false);
  const [bots, setBots] = useState<any[]>([]);
  const [newChat, setNewChat] = useState<any>({
    bot_id: '',
    telegram_chat_id: '',
    title: '',
    type_id: '',
    status_id: '',
  });
  const [saving, setSaving] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [chatToDelete, setChatToDelete] = useState<Chat | null>(null);
  const navigate = useNavigate();

  const fetchBots = async () => {
    try {
      const response = await api.get('/api/bots');
      setBots(response.data);
    } catch (error) {
      console.error('Error fetching bots:', error);
    }
  };

  useEffect(() => {
    fetchChats();
    fetchChatTypes();
    fetchChatStatuses();
    fetchBots();
  }, []);

  const fetchChats = async () => {
    try {
      const response = await api.get('/api/chats');
      setChats(response.data);
    } catch (error) {
      console.error('Error fetching chats:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchChatTypes = async () => {
    try {
      const response = await api.get('/api/chat_types');
      const map: { [key: number]: string } = {};
      response.data.forEach((type: any) => {
        map[type.type_id] = type.type_name;
      });
      setChatTypes(map);
    } catch (error) {
      console.error('Error fetching chat types:', error);
    }
  };

  const fetchChatStatuses = async () => {
    try {
      const response = await api.get('/api/chat_statuses');
      const map: { [key: number]: string } = {};
      response.data.forEach((status: any) => {
        map[status.status_id] = status.status_name;
      });
      setChatStatuses(map);
    } catch (error) {
      console.error('Error fetching chat statuses:', error);
    }
  };

  const handleCreateChat = async () => {
    setSaving(true);
    try {
      await api.post('/api/chats', {
        ...newChat,
        telegram_chat_id: Number(newChat.telegram_chat_id),
        type_id: Number(newChat.type_id),
        status_id: Number(newChat.status_id),
        bot_id: Number(newChat.bot_id),
        title: newChat.title ? [newChat.title] : [],
      });
      setOpenDialog(false);
      setNewChat({ bot_id: '', telegram_chat_id: '', title: '', type_id: '', status_id: '' });
      await fetchChats();
    } catch (error) {
      console.error('Error creating chat:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateChatField = async (chat_id: number, field: string, value: any) => {
    try {
      await api.put(`/api/chats/${chat_id}`, { [field]: value });
      await fetchChats();
    } catch (error) {
      console.error('Error updating chat:', error);
    }
  };

  const handleDeleteChat = async (chat_id: number) => {
    try {
      await api.delete(`/api/chats/${chat_id}`);
      await fetchChats();
    } catch (error) {
      console.error('Error deleting chat:', error);
    }
  };

  // Диагностика
  console.log('chatTypes', chatTypes);
  console.log('chatStatuses', chatStatuses);
  console.log('chats', chats);

  // Фильтруем чаты, чтобы не было строк без type_id или status_id
  const filteredChats = chats.filter(
    (c) => typeof c.type_id !== 'undefined' && typeof c.status_id !== 'undefined'
  );

  // Цветовая разметка строк по типу
  const getRowClassName = (params: any) => {
    // Найти название типа по type_id
    const typeName = chatTypes[params.row.type_id];
    if (typeName === 'new_chat' || typeName === 'New Chat') return 'chat-row-new';
    if (typeName === 'deleted from chat' || typeName === 'Deleted from chat' || typeName === 'blocked chat' || typeName === 'Blocked chat' || typeName === 'blocked' || typeName === 'Blocked') return 'chat-row-deleted';
    return '';
  };

  const columns: GridColDef[] = [
    { field: 'chat_id', headerName: 'ID', width: 70 },
    { field: 'telegram_chat_id', headerName: t('dashboard.chats.telegramChatId'), width: 180 },
    {
      field: 'title',
      headerName: t('dashboard.chats.title'),
      width: 200,
      renderCell: (params: any) =>
        Array.isArray(params.row.title) ? params.row.title[0] : params.row.title || '',
    },
    {
      field: 'bot_name',
      headerName: t('dashboard.chats.bot'),
      width: 160,
      sortable: true,
      filterable: true,
    },
    {
      field: 'type_id',
      headerName: t('dashboard.chats.type'),
      width: 120,
      renderCell: (params: any) => (
        <Select
          value={params.row.type_id}
          onChange={e => handleUpdateChatField(params.row.chat_id, 'type_id', e.target.value)}
          size="small"
          sx={{ minWidth: 100 }}
        >
          {Object.entries(chatTypes).map(([id, name]) => (
            <MenuItem key={id} value={Number(id)}>{name}</MenuItem>
          ))}
        </Select>
      ),
    },
    {
      field: 'status_id',
      headerName: t('dashboard.chats.status'),
      width: 120,
      renderCell: (params: any) => (
        <Select
          value={params.row.status_id}
          onChange={e => handleUpdateChatField(params.row.chat_id, 'status_id', e.target.value)}
          size="small"
          sx={{ minWidth: 100 }}
        >
          {Object.entries(chatStatuses).map(([id, name]) => (
            <MenuItem key={id} value={Number(id)}>{name}</MenuItem>
          ))}
        </Select>
      ),
    },
    { field: 'user_num', headerName: t('dashboard.chats.userNum'), width: 80 },
    { field: 'unknown_user', headerName: t('dashboard.chats.unknownUser'), width: 100 },
    {
      field: 'created_at',
      headerName: t('dashboard.chats.createdAt'),
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
      headerName: t('dashboard.chats.updatedAt'),
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
      headerName: t('dashboard.chats.actions') || 'Actions',
      width: 180,
      renderCell: (params: any) => (
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            size="small"
            variant="outlined"
            onClick={() => navigate(`/dashboard/participants/${params.row.chat_id}`)}
          >
            Участники
          </Button>
          <Button
            size="small"
            color="error"
            onClick={() => {
              setChatToDelete(params.row);
              setDeleteDialogOpen(true);
            }}
          >
            <Delete fontSize="small" />
          </Button>
        </Box>
      ),
      sortable: false,
      filterable: false,
      disableColumnMenu: true,
    },
  ];

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h4" gutterBottom>
          {t('dashboard.chats.title')}
        </Typography>
        <Button variant="contained" onClick={() => setOpenDialog(true)}>
          {t('dashboard.chats.addNew') || 'Add New Chat'}
        </Button>
      </Box>
      <Paper sx={{ height: 'calc(100vh - 200px)', width: '100%' }}>
        <DataGrid
          rows={filteredChats}
          columns={columns}
          getRowId={(row) => row.chat_id}
          getRowClassName={getRowClassName}
          initialState={{
            pagination: {
              paginationModel: { page: 0, pageSize: 10 },
            },
            sorting: {
              sortModel: [{ field: 'chat_id', sort: 'desc' }],
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
        <DialogTitle>{t('dashboard.chats.addNew') || 'Add New Chat'}</DialogTitle>
        <DialogContent>
          <FormControl fullWidth margin="dense">
            <InputLabel>{t('bots.title') || 'Bot'}</InputLabel>
            <Select
              value={newChat.bot_id}
              label={t('bots.title') || 'Bot'}
              onChange={e => setNewChat({ ...newChat, bot_id: e.target.value })}
            >
              {bots.map(bot => (
                <MenuItem key={bot.bot_id} value={bot.bot_id}>{bot.bot_name}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField
            margin="dense"
            label={t('dashboard.chats.telegramChatId') || 'Telegram Chat ID'}
            type="number"
            fullWidth
            value={newChat.telegram_chat_id}
            onChange={e => setNewChat({ ...newChat, telegram_chat_id: e.target.value })}
          />
          <TextField
            margin="dense"
            label={t('dashboard.chats.title') || 'Title'}
            type="text"
            fullWidth
            value={newChat.title}
            onChange={e => setNewChat({ ...newChat, title: e.target.value })}
          />
          <FormControl fullWidth margin="dense">
            <InputLabel>{t('dashboard.chats.type') || 'Type'}</InputLabel>
            <Select
              value={newChat.type_id}
              label={t('dashboard.chats.type') || 'Type'}
              onChange={e => setNewChat({ ...newChat, type_id: e.target.value })}
            >
              {Object.entries(chatTypes).map(([id, name]) => (
                <MenuItem key={id} value={id}>{name}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl fullWidth margin="dense">
            <InputLabel>{t('dashboard.chats.status') || 'Status'}</InputLabel>
            <Select
              value={newChat.status_id}
              label={t('dashboard.chats.status') || 'Status'}
              onChange={e => setNewChat({ ...newChat, status_id: e.target.value })}
            >
              {Object.entries(chatStatuses).map(([id, name]) => (
                <MenuItem key={id} value={id}>{name}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>{t('common.cancel') || 'Cancel'}</Button>
          <Button onClick={handleCreateChat} color="primary" disabled={saving}>
            {t('common.save') || 'Save'}
          </Button>
        </DialogActions>
      </Dialog>
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>{t('dashboard.chats.confirmDeleteTitle') || 'Удалить чат?'}</DialogTitle>
        <DialogContent>
          {t('dashboard.chats.confirmDeleteText') || 'Вы уверены, что хотите удалить этот чат?'}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>{t('common.cancel') || 'Отмена'}</Button>
          <Button
            onClick={async () => {
              if (chatToDelete) {
                await handleDeleteChat(chatToDelete.chat_id);
                setDeleteDialogOpen(false);
                setChatToDelete(null);
              }
            }}
            color="error"
          >
            {t('common.delete') || 'Удалить'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
} 