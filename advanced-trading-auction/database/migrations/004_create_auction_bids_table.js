/**
 * @param { import("knex").Knex } knex
 * @returns { Promise<void> }
 */
exports.up = function(knex) {
  return knex.schema.createTable('auction_bids', function(table) {
    table.uuid('id').primary().defaultTo(knex.raw('gen_random_uuid()'));
    table.uuid('auction_id').notNullable();
    table.uuid('bidder_id').notNullable();
    table.decimal('amount', 15, 2).notNullable();
    table.boolean('anonymous').defaultTo(false);
    table.text('message'); // Optional bid message
    table.timestamp('timestamp').defaultTo(knex.fn.now());

    // Foreign keys
    table.foreign('auction_id').references('id').inTable('auctions').onDelete('CASCADE');
    table.foreign('bidder_id').references('id').inTable('players').onDelete('CASCADE');

    // Indexes
    table.index(['auction_id', 'timestamp']);
    table.index(['bidder_id']);
    table.index(['amount']);
    table.index(['timestamp']);
  });
};

/**
 * @param { import("knex").Knex } knex
 * @returns { Promise<void> }
 */
exports.down = function(knex) {
  return knex.schema.dropTable('auction_bids');
};