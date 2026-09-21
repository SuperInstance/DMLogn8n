#!/usr/bin/env python3
"""
Google Sheets Setup Script for DMlogn8n Data Tables

This script creates and configures all the necessary Google Sheets tables
for the comprehensive data table system with proper formatting,
formulas, and data validation rules.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any
import gspread
from gspread.exceptions import SpreadsheetNotFound
from google.oauth2.service_account import Credentials

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GoogleSheetsSetup:
    """Setup and configure Google Sheets for DMlogn8n data tables"""

    def __init__(self, credentials_path: str, spreadsheet_name: str = "DMlogn8n Data Tables"):
        self.spreadsheet_name = spreadsheet_name
        self.credentials_path = credentials_path
        self.gc = None
        self.spreadsheet = None

    def authenticate(self) -> bool:
        """Authenticate with Google Sheets API"""
        try:
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            creds = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=scopes
            )
            self.gc = gspread.authorize(creds)
            logger.info("Successfully authenticated with Google Sheets API")
            return True
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False

    def create_or_open_spreadsheet(self) -> bool:
        """Create new spreadsheet or open existing one"""
        try:
            try:
                self.spreadsheet = self.gc.open(self.spreadsheet_name)
                logger.info(f"Opened existing spreadsheet: {self.spreadsheet_name}")
            except SpreadsheetNotFound:
                self.spreadsheet = self.gc.create(self.spreadsheet_name)
                logger.info(f"Created new spreadsheet: {self.spreadsheet_name}")

            # Share with current user
            self.spreadsheet.share(
                self.gc.auth.service_account_email,
                perm_type='user',
                role='writer'
            )

            return True
        except Exception as e:
            logger.error(f"Failed to create/open spreadsheet: {e}")
            return False

    def setup_character_state_table(self) -> bool:
        """Setup Character State table with proper formatting"""
        try:
            worksheet = self.spreadsheet.worksheet("Character_State") if "Character_State" in [ws.title for ws in self.spreadsheet.worksheets()] else self.spreadsheet.add_worksheet("Character_State", 1000, 20)

            # Define headers
            headers = [
                "characterId", "name", "level", "class", "hpCurrent", "hpMax",
                "mpCurrent", "mpMax", "xpCurrent", "xpToNext", "conditions",
                "inventoryWeight", "inventoryValue", "spellSlotsUsed", "spellSlotsMax",
                "lastUpdated", "sessionHistory", "notes", "metadata", "timestamp"
            ]

            # Clear and set headers
            worksheet.clear()
            worksheet.append_row(headers)

            # Format headers
            header_format = {
                "textFormat": {"bold": True},
                "backgroundColor": {"red": 0.8, "green": 0.8, "blue": 0.8},
                "borders": {
                    "top": {"style": "SOLID"},
                    "bottom": {"style": "SOLID"},
                    "left": {"style": "SOLID"},
                    "right": {"style": "SOLID"}
                }
            }

            worksheet.format("A1:T1", header_format)

            # Set column widths
            column_widths = [
                (150, "A"),  # characterId
                (200, "B"),  # name
                (80, "C"),   # level
                (150, "D"),  # class
                (100, "E"),  # hpCurrent
                (100, "F"),  # hpMax
                (100, "G"),  # mpCurrent
                (100, "H"),  # mpMax
                (120, "I"),  # xpCurrent
                (120, "J"),  # xpToNext
                (200, "K"),  # conditions
                (120, "L"),  # inventoryWeight
                (120, "M"),  # inventoryValue
                (120, "N"),  # spellSlotsUsed
                (120, "O"),  # spellSlotsMax
                (180, "P"),  # lastUpdated
                (300, "Q"),  # sessionHistory
                (200, "R"),  # notes
                (300, "S"),  # metadata
                (180, "T")   # timestamp
            ]

            for width, col in column_widths:
                worksheet.format(f"{col}:{col}", {"pixelSize": width})

            # Add data validation rules
            # Level: 1-100
            worksheet.format("C:C", {
                "dataValidation": {
                    "condition": {
                        "type": "NUMBER_BETWEEN",
                        "values": [{"userEnteredValue": 1}, {"userEnteredValue": 100}]
                    },
                    "inputMessage": "Enter level between 1 and 100",
                    "strict": True
                }
            })

            # HP/MP must be non-negative
            worksheet.format("E:H", {
                "dataValidation": {
                    "condition": {"type": "NUMBER_GREATER", "values": [{"userEnteredValue": -1}]},
                    "inputMessage": "HP/MP must be 0 or greater",
                    "strict": True
                }
            })

            # Conditional formatting for HP
            worksheet.format("E:E", {
                "conditionalFormatRules": [
                    {
                        "ranges": [{"sheetId": worksheet.id, "startRowIndex": 1, "endRowIndex": 1000, "startColumnIndex": 4, "endColumnIndex": 5}],
                        "booleanRule": {
                            "condition": {"type": "NUMBER_LESS", "values": [{"userEnteredValue": 0}]},
                            "format": {"backgroundColor": {"red": 1.0, "green": 0.8, "blue": 0.8}}
                        }
                    },
                    {
                        "ranges": [{"sheetId": worksheet.id, "startRowIndex": 1, "endRowIndex": 1000, "startColumnIndex": 4, "endColumnIndex": 5}],
                        "booleanRule": {
                            "condition": {"type": "NUMBER_LESS", "values": [{"userEnteredValue": 10}]},
                            "format": {"backgroundColor": {"red": 1.0, "green": 1.0, "blue": 0.8}}
                        }
                    }
                ]
            })

            # Add some sample data for testing
            sample_data = [
                ["char_001", "Aldric Stormwind", 5, "Fighter", 45, 50, 20, 25, 350, 500, "healthy", 15.5, 250.75, 1, 3, datetime.now().isoformat(), "[]", "", "{}", datetime.now().isoformat()],
                ["char_002", "Elara Moonwhisper", 7, "Wizard", 25, 35, 40, 45, 850, 1000, "studying", 8.2, 1800.50, 2, 4, datetime.now().isoformat(), "[]", "", "{}", datetime.now().isoformat()],
                ["char_003", "Thorne Ironforge", 4, "Cleric", 38, 42, 15, 20, 200, 400, "blessed", 25.0, 450.25, 1, 3, datetime.now().isoformat(), "[]", "", "{}", datetime.now().isoformat()]
            ]

            for row in sample_data:
                worksheet.append_row(row)

            logger.info("Character_State table setup completed")
            return True

        except Exception as e:
            logger.error(f"Failed to setup Character_State table: {e}")
            return False

    def setup_scene_state_table(self) -> bool:
        """Setup Scene State table with proper formatting"""
        try:
            worksheet = self.spreadsheet.worksheet("Scene_State") if "Scene_State" in [ws.title for ws in self.spreadsheet.worksheets()] else self.spreadsheet.add_worksheet("Scene_State", 500, 15)

            headers = [
                "sceneId", "name", "baseDescription", "lighting", "weather",
                "objects", "environmentalEffects", "timeOfDay", "visibility", "mood",
                "isDiscovered", "isExplored", "lastVisited", "lastUpdated", "timestamp"
            ]

            worksheet.clear()
            worksheet.append_row(headers)

            # Format headers
            header_format = {
                "textFormat": {"bold": True},
                "backgroundColor": {"red": 0.7, "green": 0.9, "blue": 0.7},
                "borders": {
                    "top": {"style": "SOLID"},
                    "bottom": {"style": "SOLID"},
                    "left": {"style": "SOLID"},
                    "right": {"style": "SOLID"}
                }
            }

            worksheet.format("A1:O1", header_format)

            # Set column widths
            column_widths = [
                (150, "A"),  # sceneId
                (200, "B"),  # name
                (400, "C"),  # baseDescription
                (150, "D"),  # lighting
                (150, "E"),  # weather
                (300, "F"),  # objects
                (300, "G"),  # environmentalEffects
                (150, "H"),  # timeOfDay
                (120, "I"),  # visibility
                (120, "J"),  # mood
                (100, "K"),  # isDiscovered
                (100, "L"),  # isExplored
                (180, "M"),  # lastVisited
                (180, "N"),  # lastUpdated
                (180, "O")   # timestamp
            ]

            for width, col in column_widths:
                worksheet.format(f"{col}:{col}", {"pixelSize": width})

            # Data validation for dropdown fields
            # Lighting options
            lighting_validation = {
                "condition": {"type": "ONE_OF_LIST", "values": [
                    {"userEnteredValue": "bright"},
                    {"userEnteredValue": "normal"},
                    {"userEnteredValue": "dim"},
                    {"userEnteredValue": "dark"},
                    {"userEnteredValue": "magical"},
                    {"userEnteredValue": "flickering"}
                ]},
                "inputMessage": "Select lighting condition",
                "strict": True
            }
            worksheet.format("D:D", {"dataValidation": lighting_validation})

            # Weather options
            weather_validation = {
                "condition": {"type": "ONE_OF_LIST", "values": [
                    {"userEnteredValue": "clear"},
                    {"userEnteredValue": "rain"},
                    {"userEnteredValue": "storm"},
                    {"userEnteredValue": "fog"},
                    {"userEnteredValue": "snow"},
                    {"userEnteredValue": "wind"},
                    {"userEnteredValue": "mist"}
                ]},
                "inputMessage": "Select weather condition",
                "strict": True
            }
            worksheet.format("E:E", {"dataValidation": weather_validation})

            # Sample scene data
            sample_scenes = [
                ["scene_001", "Tavern Common Room", "A warm, cozy tavern with wooden tables and a crackling fireplace.", "normal", "clear", '{"bar": {"state": "clean", "interactive": true}, "fireplace": {"state": "lit", "interactive": true}}', '[]', "evening", "good", "peaceful", "TRUE", "TRUE", datetime.now().isoformat(), datetime.now().isoformat(), datetime.now().isoformat()],
                ["scene_002", "Dark Forest Path", "A winding path through ancient, twisted trees. The air is thick with mystery.", "dim", "fog", '{"ancient_tree": {"state": "mossy", "interactive": true}, "stone_marker": {"state": "weathered", "interactive": true}}', '[{"type": "eerie_silence", "intensity": "moderate", "description": "An unnatural silence hangs in the air"}]', "night", "poor", "mysterious", "TRUE", "FALSE", datetime.now().isoformat(), datetime.now().isoformat(), datetime.now().isoformat()]
            ]

            for scene in sample_scenes:
                worksheet.append_row(scene)

            logger.info("Scene_State table setup completed")
            return True

        except Exception as e:
            logger.error(f"Failed to setup Scene_State table: {e}")
            return False

    def setup_campaign_state_table(self) -> bool:
        """Setup Campaign State table with proper formatting"""
        try:
            worksheet = self.spreadsheet.worksheet("Campaign_State") if "Campaign_State" in [ws.title for ws in self.spreadsheet.worksheets()] else self.spreadsheet.add_worksheet("Campaign_State", 100, 15)

            headers = [
                "campaignId", "locations", "npcs", "factions", "quests",
                "worldEvents", "timelineEvents", "currentInGameTime", "worldStatus",
                "partyLocation", "activeQuests", "completedQuests", "worldStatistics",
                "lastUpdated", "timestamp"
            ]

            worksheet.clear()
            worksheet.append_row(headers)

            # Format headers
            header_format = {
                "textFormat": {"bold": True},
                "backgroundColor": {"red": 0.9, "green": 0.7, "blue": 0.9},
                "borders": {
                    "top": {"style": "SOLID"},
                    "bottom": {"style": "SOLID"},
                    "left": {"style": "SOLID"},
                    "right": {"style": "SOLID"}
                }
            }

            worksheet.format("A1:O1", header_format)

            # Set column widths
            column_widths = [
                (150, "A"),  # campaignId
                (400, "B"),  # locations
                (400, "C"),  # npcs
                (400, "D"),  # factions
                (400, "E"),  # quests
                (400, "F"),  # worldEvents
                (400, "G"),  # timelineEvents
                (180, "H"),  # currentInGameTime
                (120, "I"),  # worldStatus
                (200, "J"),  # partyLocation
                (200, "K"),  # activeQuests
                (200, "L"),  # completedQuests
                (300, "M"),  # worldStatistics
                (180, "N"),  # lastUpdated
                (180, "O")   # timestamp
            ]

            for width, col in column_widths:
                worksheet.format(f"{col}:{col}", {"pixelSize": width})

            # World status validation
            status_validation = {
                "condition": {"type": "ONE_OF_LIST", "values": [
                    {"userEnteredValue": "active"},
                    {"userEnteredValue": "paused"},
                    {"userEnteredValue": "completed"},
                    {"userEnteredValue": "archived"}
                ]},
                "inputMessage": "Select world status",
                "strict": True
            }
            worksheet.format("I:I", {"dataValidation": status_validation})

            # Sample campaign data
            sample_campaign = [
                ["campaign_001",
                 '[{"id": "loc_001", "name": "Greendale Village", "type": "settlement"}]',
                 '[{"id": "npc_001", "name": "Barkeep Tom", "role": "merchant"}]',
                 '[{"id": "fac_001", "name": "Merchants Guild", "type": "organization"}]',
                 '[{"id": "quest_001", "name": "Missing Merchant", "status": "active"}]',
                 '[]',
                 '[{"id": "event_001", "type": "arrival", "description": "Party arrives in Greendale"}]',
                 "Day 1, Morning",
                 "active",
                 "scene_001",
                 '["quest_001"]',
                 '[]',
                 '{"totalLocations": 1, "totalNPCs": 1, "activeQuests": 1}',
                 datetime.now().isoformat(),
                 datetime.now().isoformat()]
            ]

            for campaign in sample_campaign:
                worksheet.append_row(campaign)

            logger.info("Campaign_State table setup completed")
            return True

        except Exception as e:
            logger.error(f"Failed to setup Campaign_State table: {e}")
            return False

    def setup_relationship_matrix_table(self) -> bool:
        """Setup Relationship Matrix table for tracking relationships"""
        try:
            worksheet = self.spreadsheet.worksheet("Relationship_Matrix") if "Relationship_Matrix" in [ws.title for ws in self.spreadsheet.worksheets()] else self.spreadsheet.add_worksheet("Relationship_Matrix", 1000, 10)

            headers = [
                "campaignId", "relationshipType", "entityId1", "entityId2", "value",
                "history", "lastModified", "modifiedBy", "reason", "timestamp"
            ]

            worksheet.clear()
            worksheet.append_row(headers)

            # Format headers
            header_format = {
                "textFormat": {"bold": True},
                "backgroundColor": {"red": 0.7, "green": 0.7, "blue": 0.9},
                "borders": {
                    "top": {"style": "SOLID"},
                    "bottom": {"style": "SOLID"},
                    "left": {"style": "SOLID"},
                    "right": {"style": "SOLID"}
                }
            }

            worksheet.format("A1:J1", header_format)

            # Set column widths
            column_widths = [
                (150, "A"),  # campaignId
                (150, "B"),  # relationshipType
                (150, "C"),  # entityId1
                (150, "D"),  # entityId2
                (100, "E"),  # value
                (400, "F"),  # history
                (180, "G"),  # lastModified
                (150, "H"),  # modifiedBy
                (300, "I"),  # reason
                (180, "J")   # timestamp
            ]

            for width, col in column_widths:
                worksheet.format(f"{col}:{col}", {"pixelSize": width})

            # Relationship value validation (-100 to 100)
            worksheet.format("E:E", {
                "dataValidation": {
                    "condition": {
                        "type": "NUMBER_BETWEEN",
                        "values": [{"userEnteredValue": -100}, {"userEnteredValue": 100}]
                    },
                    "inputMessage": "Enter relationship value between -100 (hostile) and 100 (friendly)",
                    "strict": True
                }
            })

            # Conditional formatting for relationship values
            worksheet.format("E:E", {
                "conditionalFormatRules": [
                    {
                        "ranges": [{"sheetId": worksheet.id, "startRowIndex": 1, "endRowIndex": 1000, "startColumnIndex": 4, "endColumnIndex": 5}],
                        "booleanRule": {
                            "condition": {"type": "NUMBER_GREATER_EQ", "values": [{"userEnteredValue": 50}]},
                            "format": {"backgroundColor": {"red": 0.8, "green": 1.0, "blue": 0.8}}  # Green for friendly
                        }
                    },
                    {
                        "ranges": [{"sheetId": worksheet.id, "startRowIndex": 1, "endRowIndex": 1000, "startColumnIndex": 4, "endColumnIndex": 5}],
                        "booleanRule": {
                            "condition": {"type": "NUMBER_LESS_EQ", "values": [{"userEnteredValue": -50}]},
                            "format": {"backgroundColor": {"red": 1.0, "green": 0.8, "blue": 0.8}}  # Red for hostile
                        }
                    }
                ]
            })

            # Sample relationship data
            sample_relationships = [
                ["campaign_001", "npc-npc", "npc_001", "char_001", 25, '[{"timestamp": "' + datetime.now().isoformat() + '", "change": "set", "oldValue": 0, "newValue": 25, "reason": "First meeting - neutral positive"}]', datetime.now().isoformat(), "system", "Initial relationship established", datetime.now().isoformat()],
                ["campaign_001", "character-faction", "char_001", "fac_001", 10, '[{"timestamp": "' + datetime.now().isoformat() + '", "change": "set", "oldValue": 0, "newValue": 10, "reason": "Standard faction relationship"}]', datetime.now().isoformat(), "system", "Default faction standing", datetime.now().isoformat()]
            ]

            for relationship in sample_relationships:
                worksheet.append_row(relationship)

            logger.info("Relationship_Matrix table setup completed")
            return True

        except Exception as e:
            logger.error(f"Failed to setup Relationship_Matrix table: {e}")
            return False

    def setup_sync_tables(self) -> bool:
        """Setup sync-related tables"""
        try:
            # Sync Queue table
            sync_queue = self.spreadsheet.worksheet("Sync_Queue") if "Sync_Queue" in [ws.title for ws in self.spreadsheet.worksheets()] else self.spreadsheet.add_worksheet("Sync_Queue", 1000, 12)

            sync_headers = [
                "updateId", "clientId", "dataType", "entityId", "updateData",
                "timestamp", "status", "priority", "conflictResolution",
                "processingAttempts", "lastAttempt", "resolvedAt"
            ]

            sync_queue.clear()
            sync_queue.append_row(sync_headers)

            # Sync History table
            sync_history = self.spreadsheet.worksheet("Sync_History") if "Sync_History" in [ws.title for ws in self.spreadsheet.worksheets()] else self.spreadsheet.add_worksheet("Sync_History", 5000, 10)

            history_headers = [
                "updateId", "dataType", "entityId", "updateData",
                "timestamp", "clientId", "sessionId", "status",
                "processingTime", "notes"
            ]

            sync_history.clear()
            sync_history.append_row(history_headers)

            # Rollback History table
            rollback_history = self.spreadsheet.worksheet("Rollback_History") if "Rollback_History" in [ws.title for ws in self.spreadsheet.worksheets()] else self.spreadsheet.add_worksheet("Rollback_History", 500, 12)

            rollback_headers = [
                "rollbackId", "originalUpdateId", "rollbackTargetId",
                "dataType", "entityId", "restoredData", "originalData",
                "reason", "rollbackTimestamp", "originalTimestamp",
                "restoredTimestamp", "requestedBy"
            ]

            rollback_history.clear()
            rollback_history.append_row(rollback_headers)

            logger.info("Sync tables setup completed")
            return True

        except Exception as e:
            logger.error(f"Failed to setup sync tables: {e}")
            return False

    def create_summary_dashboard(self) -> bool:
        """Create a summary dashboard with key metrics"""
        try:
            dashboard = self.spreadsheet.worksheet("Dashboard") if "Dashboard" in [ws.title for ws in self.spreadsheet.worksheets()] else self.spreadsheet.add_worksheet("Dashboard", 50, 20)

            dashboard.clear()

            # Dashboard title
            dashboard.update_acell("A1", "DMlogn8n Data Tables Dashboard")
            dashboard.format("A1:T1", {
                "textFormat": {"bold": True, "fontSize": 16},
                "backgroundColor": {"red": 0.2, "green": 0.4, "blue": 0.8},
                "horizontalAlignment": "CENTER"
            })

            # Section headers
            sections = [
                ("A3", "Character Statistics", 14),
                ("A8", "Scene Statistics", 14),
                ("E3", "Campaign Statistics", 14),
                ("E8", "Sync Statistics", 14),
                ("I3", "Recent Activity", 14),
                ("I8", "System Health", 14)
            ]

            for cell, title, size in sections:
                dashboard.update_acell(cell, title)
                dashboard.format(cell, {
                    "textFormat": {"bold": True, "fontSize": size},
                    "backgroundColor": {"red": 0.8, "green": 0.8, "blue": 0.8}
                })

            # Add formulas for statistics
            # Character stats
            dashboard.update_acell("A4", "Total Characters:")
            dashboard.update_acell("B4", "=COUNTA(Character_State!A:A)-1")
            dashboard.update_acell("A5", "Average Level:")
            dashboard.update_acell("B5", "=AVERAGE(Character_State!C:C)")
            dashboard.update_acell("A6", "Active Sessions:")
            dashboard.update_acell("B6", "=COUNTIF(Character_State!P:P, \">\" & NOW() - TIME(1,0,0))")

            # Scene stats
            dashboard.update_acell("A9", "Total Scenes:")
            dashboard.update_acell("B9", "=COUNTA(Scene_State!A:A)-1")
            dashboard.update_acell("A10", "Discovered Scenes:")
            dashboard.update_acell("B10", "=COUNTIF(Scene_State!K:K, \"TRUE\")")

            # Campaign stats
            dashboard.update_acell("E4", "Active Campaigns:")
            dashboard.update_acell("F4", "=COUNTIF(Campaign_State!I:I, \"active\")")
            dashboard.update_acell("E5", "Total Quests:")
            dashboard.update_acell("F5", "=SUM(LEN(Campaign_State!E:E)-LEN(SUBSTITUTE(Campaign_State!E:E, \"quest_\", \"\")))")
            dashboard.update_acell("E6", "Total NPCs:")
            dashboard.update_acell("F6", "=SUM(LEN(Campaign_State!C:C)-LEN(SUBSTITUTE(Campaign_State!C:C, \"npc_\", \"\")))")

            # Sync stats
            dashboard.update_acell("E9", "Pending Syncs:")
            dashboard.update_acell("F9", "=COUNTIF(Sync_Queue!G:G, \"pending\")")
            dashboard.update_acell("E10", "Conflicts Today:")
            dashboard.update_acell("F10", "=COUNTIFS(Sync_History!H:H, \"resolved\", Sync_History!E:E, \">\" & NOW() - TIME(24,0,0))")

            # Recent activity (placeholder)
            dashboard.update_acell("I4", "Last 24 Hours Updates:")
            dashboard.update_acell("I5", "=COUNTIF(Sync_History!E:E, \">\" & NOW() - TIME(24,0,0))")

            # System health
            dashboard.update_acell("I9", "System Status:")
            dashboard.update_acell("J9", "HEALTHY")
            dashboard.format("J9", {
                "textFormat": {"bold": True},
                "backgroundColor": {"red": 0.8, "green": 1.0, "blue": 0.8}
            })

            dashboard.update_acell("I10", "Last Update:")
            dashboard.update_acell("J10", "=NOW()")

            # Format dashboard cells
            dashboard.format("A4:B10, E4:F10, I4:J10", {
                "borders": {
                    "top": {"style": "SOLID"},
                    "bottom": {"style": "SOLID"},
                    "left": {"style": "SOLID"},
                    "right": {"style": "SOLID"}
                }
            })

            logger.info("Dashboard setup completed")
            return True

        except Exception as e:
            logger.error(f"Failed to setup dashboard: {e}")
            return False

    def setup_all_tables(self) -> bool:
        """Setup all tables and configurations"""
        logger.info("Starting Google Sheets setup for DMlogn8n")

        if not self.authenticate():
            return False

        if not self.create_or_open_spreadsheet():
            return False

        # Setup all tables
        tables_setup = [
            self.setup_character_state_table(),
            self.setup_scene_state_table(),
            self.setup_campaign_state_table(),
            self.setup_relationship_matrix_table(),
            self.setup_sync_tables(),
            self.create_summary_dashboard()
        ]

        if all(tables_setup):
            logger.info("All Google Sheets tables setup completed successfully!")

            # Save spreadsheet info
            with open('/home/activeloguser/DMLogn8n/google_sheets_info.json', 'w') as f:
                json.dump({
                    "spreadsheet_id": self.spreadsheet.id,
                    "spreadsheet_url": self.spreadsheet.url,
                    "spreadsheet_name": self.spreadsheet.title,
                    "setup_completed": datetime.now().isoformat()
                }, f, indent=2)

            return True
        else:
            logger.error("Some tables failed to setup")
            return False

def main():
    """Main function to run the setup"""
    # Look for credentials file
    credentials_path = os.path.expanduser("~/.config/gspread/credentials.json")

    if not os.path.exists(credentials_path):
        logger.error("Google Sheets credentials file not found!")
        logger.error(f"Please place your service account credentials at: {credentials_path}")
        return False

    # Create setup instance and run
    setup = GoogleSheetsSetup(credentials_path)
    success = setup.setup_all_tables()

    if success:
        print("\n" + "="*50)
        print("Google Sheets setup completed successfully!")
        print(f"Spreadsheet URL: {setup.spreadsheet.url}")
        print("Tables created:")
        print("  - Character_State")
        print("  - Scene_State")
        print("  - Campaign_State")
        print("  - Relationship_Matrix")
        print("  - Sync_Queue")
        print("  - Sync_History")
        print("  - Rollback_History")
        print("  - Dashboard")
        print("="*50)
    else:
        print("Setup failed. Please check the logs for details.")

    return success

if __name__ == "__main__":
    main()