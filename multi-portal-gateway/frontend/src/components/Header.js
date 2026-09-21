import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Box,
  Chip,
  Tooltip,
  Badge,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText
} from '@mui/material';
import {
  Menu as MenuIcon,
  Notifications,
  Settings,
  Circle,
  PowerSettingsNew,
  Refresh
} from '@mui/icons-material';

const Header = ({ sidebarOpen, setSidebarOpen, isConnected, systemStatus }) => {
  const [anchorEl, setAnchorEl] = React.useState(null);

  const handleMenu = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleRefresh = () => {
    window.location.reload();
  };

  return (
    <AppBar
      position="fixed"
      sx={{
        zIndex: (theme) => theme.zIndex.drawer + 1,
        transition: 'width 0.3s ease',
        width: sidebarOpen ? `calc(100% - 240px)` : '100%',
        ml: sidebarOpen ? 30 : 0,
      }}
    >
      <Toolbar>
        <IconButton
          color="inherit"
          aria-label="open drawer"
          onClick={() => setSidebarOpen(!sidebarOpen)}
          edge="start"
          sx={{
            marginRight: 2,
          }}
        >
          <MenuIcon />
        </IconButton>

        <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
          Multi-Portal Gateway System
        </Typography>

        {/* Connection Status */}
        <Box sx={{ display: 'flex', alignItems: 'center', mr: 2 }}>
          <Chip
            icon={<Circle fontSize="small" />}
            label={isConnected ? 'Connected' : 'Disconnected'}
            color={isConnected ? 'success' : 'error'}
            size="small"
            variant="outlined"
          />
        </Box>

        {/* System Status Indicator */}
        {systemStatus && (
          <Box sx={{ display: 'flex', alignItems: 'center', mr: 2 }}>
            <Tooltip title="Active Portals">
              <Badge badgeContent={systemStatus.portals?.total || 0} color="primary">
                <Chip
                  label="Portals"
                  size="small"
                  variant="outlined"
                />
              </Badge>
            </Tooltip>
          </Box>
        )}

        {/* Action Buttons */}
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Tooltip title="Refresh">
            <IconButton color="inherit" onClick={handleRefresh}>
              <Refresh />
            </IconButton>
          </Tooltip>

          <Tooltip title="Notifications">
            <IconButton color="inherit">
              <Badge badgeContent={0} color="error">
                <Notifications />
              </Badge>
            </IconButton>
          </Tooltip>

          <Tooltip title="Settings">
            <IconButton color="inherit" onClick={handleMenu}>
              <Settings />
            </IconButton>
          </Tooltip>

          <Menu
            id="menu-appbar"
            anchorEl={anchorEl}
            anchorOrigin={{
              vertical: 'top',
              horizontal: 'right',
            }}
            keepMounted
            transformOrigin={{
              vertical: 'top',
              horizontal: 'right',
            }}
            open={Boolean(anchorEl)}
            onClose={handleClose}
          >
            <MenuItem onClick={handleClose}>
              <ListItemIcon>
                <Settings fontSize="small" />
              </ListItemIcon>
              <ListItemText>Settings</ListItemText>
            </MenuItem>
            <MenuItem onClick={handleClose}>
              <ListItemIcon>
                <PowerSettingsNew fontSize="small" />
              </ListItemIcon>
              <ListItemText>Shutdown System</ListItemText>
            </MenuItem>
          </Menu>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header;