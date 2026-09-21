/**
 * Conversational Combat System - Main Entry Point
 * Revolutionary dialogue-driven combat mechanics for D&D 5e
 */

// Main system exports
export { ConversationalCombatSystem } from './core/conversational-combat-system';

// Core component exports
export { DialogueToActionParser } from './parsers/dialogue-to-action-parser';
export { StrategicDialogueMechanics } from './mechanics/strategic-dialogue-mechanics';
export { CombatNarrativeEngine } from './narrative/combat-narrative-engine';
export { DialogueCombatIntegration } from './integration/dialogue-combat-integration';
export { DialogueEnhancement } from './ai/dialogue-enhancement';

// Type exports
export * from './types';

// Utility exports
export * from './utils/constants';

// Default export
import { ConversationalCombatSystem } from './core/conversational-combat-system';
export default ConversationalCombatSystem;

/**
 * Quick start example:
 *
 * ```typescript
 * import ConversationalCombatSystem from './conversational-combat';
 *
 * // Initialize system with combat context
 * const system = new ConversationalCombatSystem(combatContext);
 *
 * // Process dialogue in combat
 * const result = await system.processDialogue('character123', 'I will strike you down with righteous fury!');
 *
 * // Get tactical suggestions
 * const suggestions = await system.getTacticalSuggestions('character123');
 *
 * // Generate spectator narrative
 * const narrative = system.generateSpectatorNarrative('last_round');
 * ```
 */