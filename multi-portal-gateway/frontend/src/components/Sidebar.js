import React from 'react';
import {
  Drawer,
  Box,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  Typography,
  Chip,
  Collapse,
  ListSubheader
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  People as PeopleIcon,
  Casino as CasinoIcon,
  Code as CodeIcon,
  Monitor as MonitorIcon,
  Settings as SettingsIcon,
  ExpandLess,
  ExpandMore,
  Add as AddIcon,
  PlayArrow as PlayIcon
} from '@mui/icons-material';

const drawerWidth = 240;

const Sidebar = ({ open, onNavigate, onPortalSelect, currentView, systemStatus }) => {
  const [portalsOpen, setPortalsOpen] = React.useState(true);

  const handlePortalsToggle = () => {
    setPortalsOpen(!portalsOpen);
  };

  const menuItems = [
    {
      text: 'Dashboard',
      icon: <DashboardIcon />,
      view: 'dashboard',
      path: '/dashboard'
    },
    {
      text: 'System Monitor',
      icon: <MonitorIcon />,
      view: 'monitor',
      path: '/monitor'
    },
    {
      text: 'Settings',
      icon: <SettingsIcon />,
      view: 'settings',
      path: '/settings'
    }
  ];

  const portalTypes = [
    {
      type: 'character',
      label: 'Character Portals',
      icon: <PeopleIcon />,
      count: systemStatus?.portals?.character || 0,
      color: 'primary'
    },
    {
      type: 'dm',
      label: 'DM Portal',
      icon: <CasinoIcon />,
      count: systemStatus?.portals?.dm || 0,
      color: 'secondary'
    },
    {
      type: 'coder',
      label: 'Coder Workshop',
      icon: <CodeIcon />,
      count: systemStatus?.portals?.coder || 0,
      color: 'success'
    }
  ];

  const handlePortalClick = (type) => {
    onPortalSelect(type);

    // Navigate to appropriate portal
    if (type === 'dm') {
      window.location.href = '/dm';
    } else if (type === 'coder') {
      window.location.href = '/coder';
    }
  };

  const handleCreatePortal = (type) => {
    // This would open a dialog to create a new portal
    console.log(`Create new ${type} portal`);
    onPortalSelect(type);
  };

  return (
    <Drawer
      variant="persistent"
      anchor="left"
      open={open}
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
          borderRight: '1px solid rgba(255, 255, 255, 0.12)',
        },
      }}
    >
      <Box sx={{ overflow: 'auto', mt: 2 }}>
        {/* Navigation Menu */}
        <List>
          {menuItems.map((item) => (
            <ListItem key={item.text} disablePadding>
              <ListItemButton
                selected={currentView === item.view}
                onClick={() => onNavigate(item.view)}
                sx={{
                  '&.Mui-selected': {
                    backgroundColor: 'rgba(33, 150, 243, 0.08)',
                    borderRight: '3px solid',
                    borderRightColor: 'primary.main',
                  }
                }}
              >
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText primary={item.text} />
              </ListItemButton>
            </ListItem>
          ))}
        </List>

        <Divider sx={{ my: 2 }} />

        {/* Portal Management */}
        <List
          subheader={
            <ListSubheader
              component="div"
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                cursor: 'pointer',
                '&:hover': {
                  backgroundColor: 'rgba(255, 255, 255, 0.04)',
                }
              }}
              onClick={handlePortalsToggle}
            >
              <Typography variant="subtitle2">Portals</Typography>
              {portalsOpen ? <ExpandLess /> : <ExpandMore />}
            </ListSubheader>
          }
        >
          <Collapse in={portalsOpen} timeout="auto" unmountOnExit>
            <List component="div" disablePadding>
              {portalTypes.map((portal) => (
                <React.Fragment key={portal.type}>
                  <ListItem disablePadding>
                    <ListItemButton
                      onClick={() => handlePortalClick(portal.type)}
                      sx={{ pl: 4 }}
                    >
                      <ListItemIcon>{portal.icon}</ListItemIcon>
                      <ListItemText
                        primary={portal.label}
                        secondary={`${portal.count} active`}
                      />
                      <Chip
                        label={portal.count}
                        size="small"
                        color={portal.color}
                        variant="outlined"
                      />
                    </ListItemButton>
                  </ListItem>
                  {portal.type === 'character' && portal.count < 10 && (
                    <ListItem disablePadding>
                      <ListItemButton
                        onClick={() => handleCreatePortal(portal.type)}
                        sx={{ pl: 6 }}
                      >
                        <ListItemIcon>
                          <AddIcon fontSize="small" />
                        </ListItemIcon>
                        <ListItemText
                          primary="Create Character Portal"
                          primaryTypographyProps={{ variant: 'caption' }}
                        />
                      </ListItemButton>
                    </ListItem>
                  )}
                  {portal.type === 'dm' && portal.count === 0 && (
                    <ListItem disablePadding>
                      <ListItemButton
                        onClick={() => handleCreatePortal(portal.type)}
                        sx={{ pl: 6 }}
                      >
                        <ListItemIcon>
                          <AddIcon fontSize="small" />
                        </ListItemIcon>
                        <ListItemText
                          primary="Start DM Portal"
                          primaryTypographyProps={{ variant: 'caption' }}
                        />
                      </ListItemButton>
                    </ListItem>
                  )}
                  {portal.type === 'coder' && portal.count === 0 && (
                    <ListItem disablePadding>
                      <ListItemButton
                        onClick={() => handleCreatePortal(portal.type)}
                        sx={{ pl: 6 }}
                      >
                        <ListItemIcon>
                          <AddIcon fontSize="small" />
                        </ListItemIcon>
                        <ListItemText
                          primary="Start Coder Workshop"
                          primaryTypographyProps={{ variant: 'caption' }}
                        />
                      </ListItemButton>
                    </ListItem>
                  )}
                </React.Fragment>
              ))}
            </List>
          </Collapse>
        </List>

        <Divider sx={{ my: 2 }} />

        {/* Quick Actions */}
        <List
          subheader={
            <ListSubheader component="div">
              Quick Actions
            </ListSubheader>
          }
        >
          <ListItem disablePadding>
            <ListItemButton>
              <ListItemIcon>
                <PlayIcon />
              </ListItemIcon>
              <ListItemText
                primary="Start All Portals"
                primaryTypographyProps={{ variant: 'body2' }}
              />
            </ListItemButton>
          </ListItem>
        </List>

        {/* System Status */}
        {systemStatus && (
          <Box sx={{ p: 2, mt: 'auto' }}>
            <Typography variant="caption" color="text.secondary">
              System Status
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mt: 1 }}>
              <Chip
                label={`Connections: ${systemStatus.connections || 0}`}
                size="small"
                variant="outlined"
              />
              <Chip
                label={`Messages: ${systemStatus.messages || 0}`}
                size="small"
                variant="outlined"
              />
            </Box>
          </Box>
        )}
      </Box>
    </Drawer>
  );
};

export default Sidebar;