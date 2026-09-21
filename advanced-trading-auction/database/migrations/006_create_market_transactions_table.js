/**
 * @param { import("knex").Knex } knex
 * @returns { Promise<void> }
 */
exports.up = function(knex) {
  return knex.schema.createTable('market_transactions', function(table) {
    table.uuid('id').primary().defaultTo(knex.raw('gen_random_uuid()'));
    table.uuid('from_player_id').notNullable(); // Buyer
    table.uuid('to_player_id').notNullable(); // Seller
    table.uuid('item_id').notNullable();
    table.integer('quantity').notNullable();
    table.decimal('price', 15, 2).notNullable(); // Per-unit price
    table.decimal('total_price', 15, 2).notNullable(); // Total price
    table.decimal('fee', 15, 2).defaultTo(0); // Transaction fee
    table.enum('transaction_type', ['marketplace_sale', 'auction_sale', 'trade']).notNullable();
    table.string('region_id').notNullable().defaultTo('global');
    table.uuid('listing_id'); // Reference to marketplace listing if applicable
    table.uuid('auction_id'); // Reference to auction if applicable
    table.text('description');
    table.enum('status', ['pending', 'completed', 'failed', 'cancelled']).defaultTo('completed');
    table.json('metadata'); // Additional transaction metadata
    table.timestamp('created_at').defaultTo(knex.fn.now());

    // Foreign keys
    table.foreign('from_player_id').references('id').inTable('players').onDelete('CASCADE');
    table.foreign('to_player_id').references('id').inTable('players').onDelete('CASCADE');
    table.foreign('item_id').references('id').inTable('items').onDelete('CASCADE');
    table.foreign('listing_id').references('id').inTable('market_listings').onDelete('SET NULL');
    table.foreign('auction_id').references('id').inTable('auctions').onDelete('SET NULL');

    // Indexes
    table.index(['from_player_id']);
    table.index(['to_player_id']);
    table.index(['item_id']);
    table.index(['transaction_type']);
    table.index(['region_id']);
    table.index(['status']);
    table.index(['created_at']);
    table.index(['total_price']);
  });
};

/**
 * @param { import("knex").Knex } knex
 * @returns { Promise<void> }
 */
exports.down = function(knex) {
  return knex.schema.dropTable('market_transactions');
};