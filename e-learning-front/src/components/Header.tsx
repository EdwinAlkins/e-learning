'use client';

import { useState } from 'react';
import Image from 'next/image';
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
  Insights as InsightsIcon,
  AccountCircle as AccountCircleIcon,
  Password as PasswordIcon,
} from '@mui/icons-material';
import { useAuthStore } from '../stores/auth.store';
import { useCatalogStore } from '../stores/catalog.store';
import { useThemeStore, type ThemeMode } from '../stores/theme.store';
import { SNACKBAR_DURATION_MS } from '../constants';
import ChangePasswordDialog from './ChangePasswordDialog';

export default function Header() {
  const { user, logout } = useAuthStore();
  const { mode, setMode } = useThemeStore();
  const router = useRouter();
  const [passwordChanged, setPasswordChanged] = useState(false);
  const [passwordDialogOpen, setPasswordDialogOpen] = useState(false);
  const [themeMenuAnchor, setThemeMenuAnchor] = useState<null | HTMLElement>(null);
  const [accountMenuAnchor, setAccountMenuAnchor] = useState<null | HTMLElement>(null);

  const handleLogout = async () => {
    setAccountMenuAnchor(null);
    try {
      await logout();
    } finally {
      // Le catalogue embarque la progression du compte : ne pas la montrer au suivant.
      useCatalogStore.getState().reset();
      router.replace('/auth');
    }
  };

  const handleOpenPasswordDialog = () => {
    setAccountMenuAnchor(null);
    setPasswordDialogOpen(true);
  };

  const handleCloseSnackbar = () => {
    setPasswordChanged(false);
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
          <Box
            sx={{ display: 'flex', alignItems: 'center', gap: 1, flexGrow: 1, cursor: 'pointer' }}
            onClick={() => router.push('/')}
          >
            <Image
              src="/icon-192.png"
              alt=""
              width={32}
              height={32}
              priority
              style={{ borderRadius: 6 }}
            />
            <Typography variant="h6" component="div">
              Cladèse
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            {user?.is_admin && (
              <Button color="inherit" onClick={() => router.push('/studio')}>
                Studio
              </Button>
            )}
            <Button
              color="inherit"
              onClick={() => router.push('/usage')}
              sx={{ display: { xs: 'none', sm: 'inline-flex' } }}
            >
              Consommation
            </Button>
            <IconButton
              color="inherit"
              onClick={() => router.push('/usage')}
              aria-label="Consommation IA"
              sx={{ display: { xs: 'inline-flex', sm: 'none' } }}
            >
              <InsightsIcon />
            </IconButton>
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
            {user && (
              <>
                <Button
                  color="inherit"
                  startIcon={<AccountCircleIcon />}
                  onClick={(event) => setAccountMenuAnchor(event.currentTarget)}
                  aria-label="Mon compte"
                  sx={{ textTransform: 'none' }}
                >
                  <Box component="span" sx={{ display: { xs: 'none', sm: 'inline' } }}>
                    {user.full_name || user.email}
                  </Box>
                </Button>
                <Menu
                  anchorEl={accountMenuAnchor}
                  open={Boolean(accountMenuAnchor)}
                  onClose={() => setAccountMenuAnchor(null)}
                  anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                  transformOrigin={{ vertical: 'top', horizontal: 'right' }}
                >
                  <MenuItem disabled>
                    <ListItemText
                      primary={user.email}
                      secondary={user.is_admin ? 'Administrateur' : 'Apprenant'}
                    />
                  </MenuItem>
                  <MenuItem onClick={handleOpenPasswordDialog}>
                    <ListItemIcon>
                      <PasswordIcon fontSize="small" />
                    </ListItemIcon>
                    <ListItemText>Changer le mot de passe</ListItemText>
                  </MenuItem>
                  <MenuItem onClick={handleLogout}>
                    <ListItemIcon>
                      <LogoutIcon fontSize="small" />
                    </ListItemIcon>
                    <ListItemText>Déconnexion</ListItemText>
                  </MenuItem>
                </Menu>
              </>
            )}
          </Box>
        </Toolbar>
      </AppBar>
      <ChangePasswordDialog
        open={passwordDialogOpen}
        onClose={() => setPasswordDialogOpen(false)}
        onChanged={() => {
          setPasswordDialogOpen(false);
          setPasswordChanged(true);
        }}
      />
      <Snackbar
        open={passwordChanged}
        autoHideDuration={SNACKBAR_DURATION_MS}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseSnackbar} severity="success" sx={{ width: '100%' }}>
          Mot de passe modifié
        </Alert>
      </Snackbar>
    </>
  );
}
