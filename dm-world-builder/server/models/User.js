const mongoose = require('mongoose');

const userSchema = new mongoose.Schema({
  id: { type: String, required: true, unique: true },
  name: { type: String, required: true, trim: true },
  email: { type: String, required: true, unique: true, trim: true, lowercase: true },
  password: { type: String, required: true },
  avatar: { type: String, default: null },
  preferences: {
    theme: { type: String, enum: ['light', 'dark', 'auto'], default: 'dark' },
    language: { type: String, default: 'en' },
    notifications: {
      email: { type: Boolean, default: true },
      push: { type: Boolean, default: true },
      campaign: { type: Boolean, default: true },
      character: { type: Boolean, default: true },
      session: { type: Boolean, default: true }
    },
    dashboard: {
      layout: { type: String, default: 'grid' },
      widgets: [String]
    }
  },
  subscription: {
    tier: { type: String, enum: ['free', 'pro', 'premium'], default: 'free' },
    startDate: { type: Date },
    endDate: { type: Date },
    autoRenew: { type: Boolean, default: false }
  },
  stats: {
    campaignsCreated: { type: Number, default: 0 },
    sessionsPlayed: { type: Number, default: 0 },
    charactersCreated: { type: Number, default: 0 },
    totalPlaytime: { type: Number, default: 0 } // in minutes
  },
  resetPasswordToken: { type: String },
  resetPasswordExpires: { type: Date },
  emailVerified: { type: Boolean, default: false },
  emailVerificationToken: { type: String },
  lastLogin: { type: Date },
  isActive: { type: Boolean, default: true },
  isDeleted: { type: Boolean, default: false },
  createdAt: { type: Date, default: Date.now },
  updatedAt: { type: Date, default: Date.now }
});

// Indexes
userSchema.index({ email: 1 });
userSchema.index({ id: 1 });
userSchema.index({ createdAt: -1 });
userSchema.index({ lastLogin: -1 });

// Pre-save middleware
userSchema.pre('save', function(next) {
  this.updatedAt = new Date();
  next();
});

// Methods
userSchema.methods.toSafeObject = function() {
  return {
    id: this.id,
    name: this.name,
    email: this.email,
    avatar: this.avatar,
    preferences: this.preferences,
    subscription: this.subscription,
    stats: this.stats,
    emailVerified: this.emailVerified,
    lastLogin: this.lastLogin,
    isActive: this.isActive,
    createdAt: this.createdAt,
    updatedAt: this.updatedAt
  };
};

// Static methods
userSchema.statics.findByEmail = function(email) {
  return this.findOne({ email: email.toLowerCase(), isDeleted: false });
};

userSchema.statics.findByIdActive = function(id) {
  return this.findOne({ id, isActive: true, isDeleted: false });
};

module.exports = mongoose.model('User', userSchema);