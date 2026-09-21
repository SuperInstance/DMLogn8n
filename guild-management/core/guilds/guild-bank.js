/**
 * Guild Bank System
 * Manages guild bank storage, transactions, and permissions
 */

class GuildBank {
    constructor(databaseClient, inventoryService, notificationService) {
        this.db = databaseClient;
        this.inventory = inventoryService;
        this.notifications = notificationService;
        this.bankCache = new Map();
        this.transactionLimits = new Map();
    }

    /**
     * Get guild bank information
     */
    async getGuildBank(guildId) {
        try {
            // Check cache first
            if (this.bankCache.has(guildId)) {
                return this.bankCache.get(guildId);
            }

            const bank = await this.db.collection('guild_banks').findOne({ guildId: guildId });
            if (bank) {
                this.bankCache.set(guildId, bank);
            }
            return bank;
        } catch (error) {
            console.error('Error fetching guild bank:', error);
            return null;
        }
    }

    /**
     * Deposit gold to guild bank
     */
    async depositGold(guildId, playerId, amount, note = '') {
        try {
            // Validate amount
            if (amount <= 0) {
                throw new Error('Deposit amount must be positive');
            }

            // Get player and validate funds
            const player = await this.getPlayerData(playerId);
            if (!player || player.gold < amount) {
                throw new Error('Insufficient funds');
            }

            // Get guild bank
            const bank = await this.getGuildBank(guildId);
            if (!bank) {
                throw new Error('Guild bank not found');
            }

            // Check deposit permissions
            const member = await this.getGuildMember(guildId, playerId);
            if (!this.hasPermission(member, 'deposit_bank')) {
                throw new Error('No permission to deposit to guild bank');
            }

            // Process transaction
            await this.deductPlayerGold(playerId, amount);
            await this.addBankGold(guildId, amount);

            // Record transaction
            const transaction = {
                id: this.generateTransactionId(),
                type: 'deposit',
                guildId: guildId,
                playerId: playerId,
                amount: amount,
                itemType: 'gold',
                note: note,
                timestamp: new Date().toISOString(),
                approvedBy: 'auto'
            };

            await this.recordTransaction(transaction);

            // Update cache
            bank.gold += amount;
            this.bankCache.set(guildId, bank);

            // Notify guild
            await this.notifyGuild(guildId, {
                type: 'bank_deposit',
                playerId: playerId,
                amount: amount,
                note: note
            });

            return {
                success: true,
                transaction: transaction,
                newBalance: bank.gold
            };

        } catch (error) {
            console.error('Error depositing gold:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Withdraw gold from guild bank
     */
    async withdrawGold(guildId, playerId, amount, reason = '') {
        try {
            // Validate amount
            if (amount <= 0) {
                throw new Error('Withdrawal amount must be positive');
            }

            // Get guild bank
            const bank = await this.getGuildBank(guildId);
            if (!bank) {
                throw new Error('Guild bank not found');
            }

            if (bank.gold < amount) {
                throw new Error('Insufficient guild bank funds');
            }

            // Check withdrawal permissions and limits
            const member = await this.getGuildMember(guildId, playerId);
            if (!this.hasPermission(member, 'withdraw_bank')) {
                throw new Error('No permission to withdraw from guild bank');
            }

            // Check daily withdrawal limits
            const dailyLimit = await this.checkDailyLimit(guildId, playerId, amount);
            if (!dailyLimit.allowed) {
                throw new Error(dailyLimit.reason);
            }

            // Check if approval is needed for large withdrawals
            const approvalNeeded = await this.checkApprovalNeeded(guildId, playerId, amount);
            if (approvalNeeded.needed) {
                return await this.createWithdrawalRequest(guildId, playerId, amount, reason, 'gold');
            }

            // Process withdrawal
            await this.addPlayerGold(playerId, amount);
            await this.deductBankGold(guildId, amount);

            // Record transaction
            const transaction = {
                id: this.generateTransactionId(),
                type: 'withdrawal',
                guildId: guildId,
                playerId: playerId,
                amount: amount,
                itemType: 'gold',
                reason: reason,
                timestamp: new Date().toISOString(),
                approvedBy: 'auto'
            };

            await this.recordTransaction(transaction);

            // Update cache
            bank.gold -= amount;
            this.bankCache.set(guildId, bank);

            // Notify guild officers
            await this.notifyOfficers(guildId, {
                type: 'bank_withdrawal',
                playerId: playerId,
                amount: amount,
                reason: reason,
                transactionId: transaction.id
            });

            return {
                success: true,
                transaction: transaction,
                newBalance: bank.gold
            };

        } catch (error) {
            console.error('Error withdrawing gold:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Deposit item to guild bank
     */
    async depositItem(guildId, playerId, itemId, quantity = 1, tabId = null, note = '') {
        try {
            // Validate item and quantity
            if (quantity <= 0) {
                throw new Error('Quantity must be positive');
            }

            // Get player inventory
            const playerItem = await this.inventory.getPlayerItem(playerId, itemId);
            if (!playerItem || playerItem.quantity < quantity) {
                throw new Error('Item not found or insufficient quantity');
            }

            // Get guild bank
            const bank = await this.getGuildBank(guildId);
            if (!bank) {
                throw new Error('Guild bank not found');
            }

            // Check deposit permissions
            const member = await this.getGuildMember(guildId, playerId);
            if (!this.hasPermission(member, 'deposit_bank')) {
                throw new Error('No permission to deposit to guild bank');
            }

            // Determine target tab
            const targetTab = tabId || await this.getDefaultDepositTab(guildId, itemId);
            const bankTab = bank.tabs.find(t => t.id === targetTab);
            if (!bankTab) {
                throw new Error('Bank tab not found');
            }

            // Check tab permissions
            if (!this.hasTabPermission(member, bankTab, 'deposit')) {
                throw new Error('No permission to deposit to this tab');
            }

            // Check if tab has space
            if (!await this.hasTabSpace(bankTab, itemId, quantity)) {
                throw new Error('Bank tab is full');
            }

            // Process transaction
            await this.inventory.removePlayerItem(playerId, itemId, quantity);
            await this.addBankItem(guildId, targetTab, itemId, quantity);

            // Record transaction
            const transaction = {
                id: this.generateTransactionId(),
                type: 'deposit',
                guildId: guildId,
                playerId: playerId,
                itemId: itemId,
                quantity: quantity,
                itemType: 'item',
                tabId: targetTab,
                note: note,
                timestamp: new Date().toISOString(),
                approvedBy: 'auto'
            };

            await this.recordTransaction(transaction);

            // Update cache
            this.bankCache.set(guildId, bank);

            // Notify guild
            await this.notifyGuild(guildId, {
                type: 'bank_deposit',
                playerId: playerId,
                itemId: itemId,
                quantity: quantity,
                tabId: targetTab,
                note: note
            });

            return {
                success: true,
                transaction: transaction,
                bankTab: targetTab
            };

        } catch (error) {
            console.error('Error depositing item:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Withdraw item from guild bank
     */
    async withdrawItem(guildId, playerId, itemId, quantity = 1, tabId, reason = '') {
        try {
            // Validate quantity
            if (quantity <= 0) {
                throw new Error('Quantity must be positive');
            }

            // Get guild bank
            const bank = await this.getGuildBank(guildId);
            if (!bank) {
                throw new Error('Guild bank not found');
            }

            const bankTab = bank.tabs.find(t => t.id === tabId);
            if (!bankTab) {
                throw new Error('Bank tab not found');
            }

            // Check if item exists in bank
            const bankItem = bankTab.items.find(item => item.itemId === itemId);
            if (!bankItem || bankItem.quantity < quantity) {
                throw new Error('Item not found in guild bank or insufficient quantity');
            }

            // Check withdrawal permissions
            const member = await this.getGuildMember(guildId, playerId);
            if (!this.hasPermission(member, 'withdraw_bank')) {
                throw new Error('No permission to withdraw from guild bank');
            }

            // Check tab permissions
            if (!this.hasTabPermission(member, bankTab, 'withdraw')) {
                throw new Error('No permission to withdraw from this tab');
            }

            // Check daily withdrawal limits
            const dailyLimit = await this.checkDailyLimit(guildId, playerId, quantity, 'items');
            if (!dailyLimit.allowed) {
                throw new Error(dailyLimit.reason);
            }

            // Check if approval is needed for valuable items
            const approvalNeeded = await this.checkItemApprovalNeeded(guildId, playerId, itemId, quantity);
            if (approvalNeeded.needed) {
                return await this.createWithdrawalRequest(guildId, playerId, quantity, reason, 'item', {
                    itemId: itemId,
                    tabId: tabId
                });
            }

            // Process withdrawal
            await this.inventory.addPlayerItem(playerId, itemId, quantity);
            await this.removeBankItem(guildId, tabId, itemId, quantity);

            // Record transaction
            const transaction = {
                id: this.generateTransactionId(),
                type: 'withdrawal',
                guildId: guildId,
                playerId: playerId,
                itemId: itemId,
                quantity: quantity,
                itemType: 'item',
                tabId: tabId,
                reason: reason,
                timestamp: new Date().toISOString(),
                approvedBy: 'auto'
            };

            await this.recordTransaction(transaction);

            // Update cache
            this.bankCache.set(guildId, bank);

            // Notify guild officers
            await this.notifyOfficers(guildId, {
                type: 'bank_withdrawal',
                playerId: playerId,
                itemId: itemId,
                quantity: quantity,
                tabId: tabId,
                reason: reason,
                transactionId: transaction.id
            });

            return {
                success: true,
                transaction: transaction,
                item: bankItem
            };

        } catch (error) {
            console.error('Error withdrawing item:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Move items between bank tabs
     */
    async moveItem(guildId, playerId, itemId, quantity, fromTabId, toTabId) {
        try {
            const bank = await this.getGuildBank(guildId);
            if (!bank) {
                throw new Error('Guild bank not found');
            }

            const fromTab = bank.tabs.find(t => t.id === fromTabId);
            const toTab = bank.tabs.find(t => t.id === toTabId);

            if (!fromTab || !toTab) {
                throw new Error('Bank tab not found');
            }

            // Check permissions
            const member = await this.getGuildMember(guildId, playerId);
            if (!this.hasPermission(member, 'manage_bank')) {
                throw new Error('No permission to manage guild bank');
            }

            // Check source tab has item
            const sourceItem = fromTab.items.find(item => item.itemId === itemId);
            if (!sourceItem || sourceItem.quantity < quantity) {
                throw new Error('Item not found or insufficient quantity');
            }

            // Check destination tab has space
            if (!await this.hasTabSpace(toTab, itemId, quantity)) {
                throw new Error('Destination tab is full');
            }

            // Move item
            await this.removeBankItem(guildId, fromTabId, itemId, quantity);
            await this.addBankItem(guildId, toTabId, itemId, quantity);

            // Record transaction
            const transaction = {
                id: this.generateTransactionId(),
                type: 'move',
                guildId: guildId,
                playerId: playerId,
                itemId: itemId,
                quantity: quantity,
                itemType: 'item',
                fromTabId: fromTabId,
                toTabId: toTabId,
                timestamp: new Date().toISOString()
            };

            await this.recordTransaction(transaction);
            this.bankCache.set(guildId, bank);

            return {
                success: true,
                transaction: transaction
            };

        } catch (error) {
            console.error('Error moving item:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Create new bank tab
     */
    async createBankTab(guildId, playerId, tabData) {
        try {
            const {
                name,
                icon,
                permissions = 'officers',
                maxSlots = 50,
                description = ''
            } = tabData;

            // Check permissions
            const member = await this.getGuildMember(guildId, playerId);
            if (!this.hasPermission(member, 'manage_bank')) {
                throw new Error('No permission to manage guild bank');
            }

            const bank = await this.getGuildBank(guildId);
            if (!bank) {
                throw new Error('Guild bank not found');
            }

            // Check max tabs limit
            if (bank.tabs.length >= 8) {
                throw new Error('Maximum number of bank tabs reached');
            }

            // Create new tab
            const newTab = {
                id: 'tab_' + Date.now(),
                name: name,
                icon: icon || '📦',
                permissions: permissions,
                items: [],
                maxSlots: maxSlots,
                description: description,
                created: new Date().toISOString(),
                createdBy: playerId
            };

            // Add to bank
            await this.db.collection('guild_banks').updateOne(
                { guildId: guildId },
                {
                    $push: { tabs: newTab },
                    $set: { lastModified: new Date().toISOString() }
                }
            );

            // Update cache
            bank.tabs.push(newTab);
            this.bankCache.set(guildId, bank);

            return {
                success: true,
                tab: newTab
            };

        } catch (error) {
            console.error('Error creating bank tab:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Get bank transaction history
     */
    async getTransactionHistory(guildId, options = {}) {
        try {
            const {
                type = null,
                playerId = null,
                itemType = null,
                startDate = null,
                endDate = null,
                limit = 50,
                offset = 0
            } = options;

            let query = { guildId: guildId };

            if (type) {
                query.type = type;
            }

            if (playerId) {
                query.playerId = playerId;
            }

            if (itemType) {
                query.itemType = itemType;
            }

            if (startDate || endDate) {
                query.timestamp = {};
                if (startDate) {
                    query.timestamp.$gte = startDate;
                }
                if (endDate) {
                    query.timestamp.$lte = endDate;
                }
            }

            const transactions = await this.db.collection('guild_bank_transactions')
                .find(query)
                .sort({ timestamp: -1 })
                .skip(offset)
                .limit(limit)
                .toArray();

            return {
                success: true,
                transactions: transactions
            };

        } catch (error) {
            console.error('Error fetching transaction history:', error);
            return {
                success: false,
                error: error.message,
                transactions: []
            };
        }
    }

    /**
     * Helper methods
     */
    generateTransactionId() {
        return 'txn_' + Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
    }

    hasPermission(member, permission) {
        return member && member.permissions && member.permissions.includes(permission);
    }

    hasTabPermission(member, tab, action) {
        const rankPermissions = {
            'Leader': true,
            'Officer': true,
            'Veteran': tab.permissions === 'members' || tab.permissions === 'veterans',
            'Member': tab.permissions === 'members',
            'Initiate': tab.permissions === 'everyone'
        };

        return rankPermissions[member.rank] || false;
    }

    async hasTabSpace(tab, itemId, quantity) {
        const existingItem = tab.items.find(item => item.itemId === itemId);
        const usedSlots = tab.items.length;

        if (existingItem) {
            return true; // Item already exists, can stack
        }

        return usedSlots < tab.maxSlots;
    }

    async getDefaultDepositTab(guildId, itemId) {
        const bank = await this.getGuildBank(guildId);
        const itemData = await this.inventory.getItemData(itemId);

        // Determine best tab based on item type
        if (itemData.type === 'equipment' || itemData.type === 'weapon') {
            const equipTab = bank.tabs.find(t => t.name.toLowerCase().includes('equipment'));
            return equipTab ? equipTab.id : bank.tabs[0].id;
        }

        if (itemData.type === 'material' || itemData.type === 'crafting') {
            const matTab = bank.tabs.find(t => t.name.toLowerCase().includes('material'));
            return matTab ? matTab.id : bank.tabs[0].id;
        }

        return bank.tabs[0].id; // Default to first tab
    }

    async checkDailyLimit(guildId, playerId, amount, type = 'gold') {
        const today = new Date().toDateString();
        const cacheKey = `${guildId}_${playerId}_${today}`;

        if (!this.transactionLimits.has(cacheKey)) {
            // Load today's transactions
            const todayTransactions = await this.db.collection('guild_bank_transactions').countDocuments({
                guildId: guildId,
                playerId: playerId,
                type: 'withdrawal',
                timestamp: {
                    $gte: new Date(today),
                    $lt: new Date(today).getTime() + 24 * 60 * 60 * 1000
                }
            });

            this.transactionLimits.set(cacheKey, todayTransactions);
        }

        const todayWithdrawals = this.transactionLimits.get(cacheKey);
        const member = await this.getGuildMember(guildId, playerId);
        const maxDaily = member.rank === 'Leader' ? 50 :
                         member.rank === 'Officer' ? 25 : 10;

        if (todayWithdrawals >= maxDaily) {
            return {
                allowed: false,
                reason: `Daily withdrawal limit of ${maxDaily} exceeded`
            };
        }

        return { allowed: true };
    }

    async checkApprovalNeeded(guildId, playerId, amount) {
        const member = await this.getGuildMember(guildId, playerId);
        const bank = await this.getGuildBank(guildId);

        // Leaders don't need approval
        if (member.rank === 'Leader') {
            return { needed: false };
        }

        // High value withdrawals need approval
        if (amount > (bank.settings.approvalThreshold || 1000)) {
            return { needed: true };
        }

        // Officers might need approval for very large amounts
        if (member.rank === 'Officer' && amount > (bank.settings.officerThreshold || 5000)) {
            return { needed: true };
        }

        return { needed: false };
    }

    async checkItemApprovalNeeded(guildId, playerId, itemId, quantity) {
        const itemData = await this.inventory.getItemData(itemId);
        const member = await this.getGuildMember(guildId, playerId);

        // Leaders don't need approval
        if (member.rank === 'Leader') {
            return { needed: false };
        }

        // Rare or epic items need approval
        if (itemData.rarity === 'rare' || itemData.rarity === 'epic' || itemData.rarity === 'legendary') {
            return { needed: true };
        }

        // High value items need approval
        if (itemData.value > 1000) {
            return { needed: true };
        }

        return { needed: false };
    }

    async createWithdrawalRequest(guildId, playerId, amount, reason, type, extraData = {}) {
        const request = {
            id: this.generateTransactionId(),
            guildId: guildId,
            playerId: playerId,
            type: 'withdrawal_request',
            amount: amount,
            itemType: type,
            reason: reason,
            status: 'pending',
            ...extraData,
            createdAt: new Date().toISOString()
        };

        await this.db.collection('guild_bank_requests').insertOne(request);

        // Notify officers for approval
        await this.notifyOfficers(guildId, {
            type: 'withdrawal_request',
            request: request
        });

        return {
            success: true,
            requiresApproval: true,
            requestId: request.id
        };
    }

    async recordTransaction(transaction) {
        await this.db.collection('guild_bank_transactions').insertOne(transaction);
    }

    async addBankGold(guildId, amount) {
        await this.db.collection('guild_banks').updateOne(
            { guildId: guildId },
            { $inc: { gold: amount } }
        );
    }

    async deductBankGold(guildId, amount) {
        await this.db.collection('guild_banks').updateOne(
            { guildId: guildId },
            { $inc: { gold: -amount } }
        );
    }

    async addBankItem(guildId, tabId, itemId, quantity) {
        await this.db.collection('guild_banks').updateOne(
            {
                guildId: guildId,
                'tabs.id': tabId
            },
            {
                $inc: { 'tabs.$.items.$[item].quantity': quantity },
                $setOnInsert: {
                    'tabs.$.items.$[item]': {
                        itemId: itemId,
                        quantity: quantity,
                        added: new Date().toISOString()
                    }
                }
            },
            {
                arrayFilters: [{ 'item.itemId': itemId }],
                upsert: true
            }
        );
    }

    async removeBankItem(guildId, tabId, itemId, quantity) {
        await this.db.collection('guild_banks').updateOne(
            {
                guildId: guildId,
                'tabs.id': tabId,
                'tabs.items.itemId': itemId
            },
            {
                $inc: { 'tabs.$.items.$[item].quantity': -quantity }
            },
            {
                arrayFilters: [{ 'item.itemId': itemId }]
            }
        );

        // Remove item if quantity reaches 0
        await this.db.collection('guild_banks').updateOne(
            {
                guildId: guildId,
                'tabs.id': tabId,
                'tabs.items.quantity': { $lte: 0 }
            },
            {
                $pull: { 'tabs.$.items': { quantity: { $lte: 0 } } }
            }
        );
    }

    async addPlayerGold(playerId, amount) {
        await this.db.collection('players').updateOne(
            { id: playerId },
            { $inc: { gold: amount } }
        );
    }

    async deductPlayerGold(playerId, amount) {
        await this.db.collection('players').updateOne(
            { id: playerId },
            { $inc: { gold: -amount } }
        );
    }

    async getGuildMember(guildId, playerId) {
        return await this.db.collection('guild_members').findOne({
            guildId: guildId,
            playerId: playerId
        });
    }

    async getPlayerData(playerId) {
        return await this.db.collection('players').findOne({ id: playerId });
    }

    async notifyGuild(guildId, message) {
        await this.notifications.sendGuildNotification(guildId, message);
    }

    async notifyOfficers(guildId, message) {
        const officers = await this.db.collection('guild_members').find({
            guildId: guildId,
            rank: { $in: ['Leader', 'Officer'] }
        }).toArray();

        for (const officer of officers) {
            await this.notifications.sendPlayerNotification(officer.playerId, message);
        }
    }
}

module.exports = GuildBank;