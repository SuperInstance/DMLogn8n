import { Request, Response, NextFunction } from 'express';

// Mock authentication middleware - replace with real auth system
export const authMiddleware = (req: Request, res: Response, next: NextFunction) => {
  // In a real implementation, this would verify JWT tokens or session cookies
  // For now, we'll add a mock user to the request

  const authHeader = req.headers.authorization;

  if (!authHeader) {
    return res.status(401).json({
      success: false,
      message: 'Authorization header required'
    });
  }

  // Mock user data - replace with real authentication logic
  req.user = {
    id: 'user_123',
    username: 'dm_user',
    role: 'dm', // Can be 'dm', 'player', or 'admin'
    permissions: ['read_learning_data', 'export_data', 'manage_agents']
  };

  next();
};

// Role-based access control middleware
export const requireRole = (roles: string[]) => {
  return (req: Request, res: Response, next: NextFunction) => {
    if (!req.user) {
      return res.status(401).json({
        success: false,
        message: 'Authentication required'
      });
    }

    if (!roles.includes(req.user.role)) {
      return res.status(403).json({
        success: false,
        message: 'Insufficient permissions'
      });
    }

    next();
  };
};

// Permission-based access control
export const requirePermission = (permission: string) => {
  return (req: Request, res: Response, next: NextFunction) => {
    if (!req.user) {
      return res.status(401).json({
        success: false,
        message: 'Authentication required'
      });
    }

    if (!req.user.permissions.includes(permission)) {
      return res.status(403).json({
        success: false,
        message: `Permission '${permission}' required`
      });
    }

    next();
  };
};

// Extend Express Request type to include user
declare global {
  namespace Express {
    interface Request {
      user?: {
        id: string;
        username: string;
        role: string;
        permissions: string[];
      };
    }
  }
}