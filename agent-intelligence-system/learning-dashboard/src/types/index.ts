// Core types for the Agent Intelligence Learning Dashboard

export interface AgentLearningMetrics {
  agentId: string;
  agentName: string;
  characterClass: string;
  level: number;

  // Intelligence Quotient metrics
  intelligenceMetrics: {
    currentIQ: number;
    baselineIQ: number;
    iqProgression: IQDataPoint[];
    learningVelocity: number;
    retentionRate: number;
    adaptiveThinkingScore: number;
  };

  // Memory system metrics
  memoryMetrics: {
    totalMemories: number;
    memoryCapacity: number;
    memoryUtilization: number;
    episodicMemories: MemoryTypeMetrics;
    semanticMemories: MemoryTypeMetrics;
    proceduralMemories: MemoryTypeMetrics;
    socialMemories: MemoryTypeMetrics;
    consolidationRate: number;
    accessPatterns: MemoryAccessPattern[];
  };

  // Skill development metrics
  skillMetrics: {
    combatSkills: SkillProgress[];
    socialSkills: SkillProgress[];
    explorationSkills: SkillProgress[];
    strategicSkills: SkillProgress[];
    technicalSkills: SkillProgress[];
    totalSkillPoints: number;
    skillVelocity: number;
    masteryDistribution: MasteryLevel[];
  };

  // Learning patterns and insights
  learningInsights: {
    recentLessons: LearningLesson[];
    patternRecognitions: PatternRecognition[];
    strategicImprovements: StrategicImprovement[];
    failureAnalysis: FailureAnalysis[];
    successPatterns: SuccessPattern[];
    adaptiveStrategies: AdaptiveStrategy[];
  };

  // Performance benchmarks
  performanceBenchmarks: {
    baselineComparison: BaselineComparison;
    peerComparison: PeerComparison;
    personalBests: PersonalBest[];
    improvementRate: number;
    consistencyScore: number;
  };

  // Meta-learning metrics
  metaLearningMetrics: {
    selfReflectionQuality: number;
    learningEfficiency: number;
    knowledgeTransfer: number;
    metaCognitionScore: number;
    adaptiveLearningRate: number;
  };
}

export interface IQDataPoint {
  timestamp: Date;
  iq: number;
  sessionId: string;
  testType: 'strategic' | 'tactical' | 'social' | 'comprehensive';
  confidence: number;
}

export interface MemoryTypeMetrics {
  count: number;
  capacity: number;
  averageImportance: number;
  consolidationRate: number;
  retentionRate: number;
  lastAccessed: Date;
}

export interface MemoryAccessPattern {
  memoryType: string;
  accessFrequency: number;
  accessRecency: Date;
  importanceScore: number;
  retrievalAccuracy: number;
}

export interface SkillProgress {
  skillId: string;
  skillName: string;
  skillType: SkillType;
  currentLevel: number;
  currentXP: number;
  nextLevelXP: number;
  totalXP: number;
  progressRate: number;
  masteryLevel: MasteryLevel;
  specializations: string[];
  lastUsed: Date;
  successRate: number;
}

export type SkillType = 'combat' | 'social' | 'exploration' | 'strategic' | 'technical';

export type MasteryLevel = 'novice' | 'apprentice' | 'journeyman' | 'expert' | 'master';

export interface LearningLesson {
  id: string;
  timestamp: Date;
  lessonType: 'success' | 'failure' | 'insight' | 'breakthrough';
  category: string;
  title: string;
  description: string;
  impact: number;
  context: string;
  appliedIn: string[];
  retentionScore: number;
}

export interface PatternRecognition {
  id: string;
  patternType: 'behavioral' | 'strategic' | 'social' | 'environmental';
  description: string;
  frequency: number;
  successRate: number;
  contexts: string[];
  firstObserved: Date;
  confidence: number;
}

export interface StrategicImprovement {
  id: string;
  area: string;
  beforeScore: number;
  afterScore: number;
  improvementType: 'quantitative' | 'qualitative';
  description: string;
  contributingFactors: string[];
  measuredAt: Date;
}

export interface FailureAnalysis {
  id: string;
  timestamp: Date;
  situation: string;
  attemptedAction: string;
  failureReason: string;
  lessonsLearned: string[];
  preventionStrategies: string[];
  recoveryActions: string[];
  similarFailures: number;
}

export interface SuccessPattern {
  id: string;
  pattern: string;
  successRate: number;
  contexts: string[];
  contributingFactors: string[];
  repeatability: number;
  lastExecuted: Date;
}

export interface AdaptiveStrategy {
  id: string;
  strategyName: string;
  description: string;
  effectivenessScore: number;
  adaptationCount: number;
  successContexts: string[];
  failureContexts: string[];
  evolutionHistory: StrategyEvolution[];
}

export interface StrategyEvolution {
  timestamp: Date;
  changeDescription: string;
  effectivenessBefore: number;
  effectivenessAfter: number;
  triggerEvent: string;
}

export interface BaselineComparison {
  baselineIQ: number;
  currentIQ: number;
  improvementPercentage: number;
  skillImprovements: Record<string, number>;
  memoryEfficiencyImprovement: number;
  learningVelocityImprovement: number;
}

export interface PeerComparison {
  percentileRank: number;
  totalAgents: number;
  aboveAverageIn: string[];
  belowAverageIn: string[];
  topPerformers: AgentComparison[];
}

export interface AgentComparison {
  agentId: string;
  agentName: string;
  metricName: string;
  value: number;
  rank: number;
}

export interface PersonalBest {
  metric: string;
  value: number;
  achievedAt: Date;
  sessionId: string;
  context: string;
}

export interface LearningSession {
  id: string;
  agentId: string;
  startTime: Date;
  endTime: Date;
  duration: number;
  experiences: Experience[];
  lessonsLearned: string[];
  skillsImproved: string[];
  iqBefore: number;
  iqAfter: number;
  overallSuccess: number;
}

export interface Experience {
  id: string;
  timestamp: Date;
  situation: string;
  action: string;
  outcome: string;
  success: boolean;
  lessons: string[];
  skillsUsed: string[];
  impact: number;
}

export interface LearningMilestone {
  id: string;
  title: string;
  description: string;
  category: 'iq' | 'skill' | 'memory' | 'strategy' | 'meta-learning';
  criteria: MilestoneCriteria;
  achieved: boolean;
  achievedAt?: Date;
  rewards: MilestoneReward[];
}

export interface MilestoneCriteria {
  metric: string;
  value: number;
  comparison: 'equals' | 'greater_than' | 'less_than' | 'percentage_improvement';
  timeframe?: string;
}

export interface MilestoneReward {
  type: 'badge' | 'title' | 'ability_unlock' | 'memory_capacity' | 'skill_bonus';
  description: string;
  value: string | number;
}

export interface DashboardConfig {
  refreshInterval: number;
  timeframes: TimeframeConfig[];
  alertThresholds: AlertThreshold[];
  exportFormats: string[];
  chartPreferences: ChartPreferences;
}

export interface TimeframeConfig {
  id: string;
  label: string;
  duration: number;
  unit: 'hours' | 'days' | 'weeks' | 'months';
}

export interface AlertThreshold {
  metric: string;
  condition: 'above' | 'below' | 'equals';
  value: number;
  severity: 'info' | 'warning' | 'critical';
  message: string;
}

export interface ChartPreferences {
  colorScheme: string;
  animationEnabled: boolean;
  showDataLabels: boolean;
  chartType: 'line' | 'bar' | 'radar' | 'scatter' | 'heatmap';
}

export interface WebSocketMessage {
  type: 'metric_update' | 'milestone_achieved' | 'session_complete' | 'alert';
  data: any;
  timestamp: Date;
  agentId: string;
}

// API Response types
export interface LearningDataResponse {
  success: boolean;
  data: AgentLearningMetrics;
  message?: string;
  timestamp: Date;
}

export interface HistoricalDataResponse {
  success: boolean;
  data: {
    daily: AgentLearningMetrics[];
    weekly: AgentLearningMetrics[];
    monthly: AgentLearningMetrics[];
  };
  timeframe: string;
}

export interface ComparisonResponse {
  success: boolean;
  data: {
    before: AgentLearningMetrics;
    after: AgentLearningMetrics;
    improvements: Record<string, number>;
    analysis: string;
  };
}

export interface ExportResponse {
  success: boolean;
  downloadUrl: string;
  filename: string;
  format: string;
  size: number;
  expiresAt: Date;
}