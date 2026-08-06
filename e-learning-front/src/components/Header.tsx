'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  Snackbar,
  Alert,
  IconButton,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  Logout as LogoutIcon,
  LightMode as LightModeIcon,
  DarkMode as DarkModeIcon,
  SettingsBrightness as SettingsBrightnessIcon,
} from '@mui/icons-material';
import { useAuthStore } from '../stores/auth.store';
import { useThemeStore, type ThemeMode } from '../stores/theme.store';
import { SNACKBAR_DURATION_MS } from '../constants';

export default function Header() {
  const { uid, clearUID } = useAuthStore();
  const { mode, setMode } = useThemeStore();
  const router = useRouter();
  const [copied, setCopied] = useState(false);
  const [themeMenuAnchor, setThemeMenuAnchor] = useState<null | HTMLElement>(null);

  const handleLogout = () => {
    clearUID();
    router.push('/auth');
  };

  const handleCopyUID = async () => {
    if (!uid) return;

    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(uid);
        setCopied(true);
        return;
      }

      // Fallback : execCommand quand l'API Clipboard est indisponible
      const textArea = document.createElement('textarea');
      textArea.value = uid;
      textArea.setAttribute('readonly', '');
      textArea.style.position = 'fixed';
      textArea.style.left = '-999999px';
      document.body.appendChild(textArea);
      textArea.select();
      try {
        const ok = document.execCommand('copy');
        if (ok) setCopied(true);
      } finally {
        document.body.removeChild(textArea);
      }
    } catch (err) {
      console.error('Failed to copy UID:', err);
    }
  };

  const handleCloseSnackbar = () => {
    setCopied(false);
  };

  const handleThemeMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setThemeMenuAnchor(event.currentTarget);
  };

  const handleThemeMenuClose = () => {
    setThemeMenuAnchor(null);
  };

  const handleThemeChange = (newMode: ThemeMode) => {
    setMode(newMode);
    handleThemeMenuClose();
  };

  const getThemeIcon = () => {
    switch (mode) {
      case 'light':
        return <LightModeIcon />;
      case 'dark':
        return <DarkModeIcon />;
      case 'system':
        return <SettingsBrightnessIcon />;
    }
  };

  return (
    <>
      <AppBar position="static">
        <Toolbar>
          <Typography
            variant="h6"
            component="div"
            sx={{ flexGrow: 1, cursor: 'pointer' }}
            onClick={() => router.push('/')}
          >
            Formation
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Button color="inherit" onClick={() => router.push('/studio')}>
              Studio
            </Button>
            <IconButton color="inherit" onClick={handleThemeMenuOpen} aria-label="Changer le thème">
              {getThemeIcon()}
            </IconButton>
            <Menu
              anchorEl={themeMenuAnchor}
              open={Boolean(themeMenuAnchor)}
              onClose={handleThemeMenuClose}
              anchorOrigin={{
                vertical: 'bottom',
                horizontal: 'right',
              }}
              transformOrigin={{
                vertical: 'top',
                horizontal: 'right',
              }}
            >
              <MenuItem onClick={() => handleThemeChange('light')} selected={mode === 'light'}>
                <ListItemIcon>
                  <LightModeIcon fontSize="small" />
                </ListItemIcon>
                <ListItemText>Clair</ListItemText>
              </MenuItem>
              <MenuItem onClick={() => handleThemeChange('dark')} selected={mode === 'dark'}>
                <ListItemIcon>
                  <DarkModeIcon fontSize="small" />
                </ListItemIcon>
                <ListItemText>Sombre</ListItemText>
              </MenuItem>
              <MenuItem onClick={() => handleThemeChange('system')} selected={mode === 'system'}>
                <ListItemIcon>
                  <SettingsBrightnessIcon fontSize="small" />
                </ListItemIcon>
                <ListItemText>Système</ListItemText>
              </MenuItem>
            </Menu>
            {uid && (
              <>
                <Typography
                  variant="body2"
                  sx={{
                    display: { xs: 'none', sm: 'block' },
                    cursor: 'pointer',
                    '&:hover': {
                      textDecoration: 'underline',
                    },
                  }}
                  onClick={handleCopyUID}
                >
                  UID: {uid}
                </Typography>
                <Button
                  color="inherit"
                  startIcon={<LogoutIcon />}
                  onClick={handleLogout}
                >
                  Déconnexion
                </Button>
              </>
            )}
          </Box>
        </Toolbar>
      </AppBar>
      <Snackbar
        open={copied}
        autoHideDuration={SNACKBAR_DURATION_MS}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseSnackbar} severity="success" sx={{ width: '100%' }}>
          UID copié dans le presse-papiers
        </Alert>
      </Snackbar>
    </>
  );
}
