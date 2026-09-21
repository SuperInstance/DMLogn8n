/**
 * @param { import("knex").Knex } knex
 * @returns { Promise<void> }
 */
exports.up = function(knex) {
  return knex.schema.createTable('market_prices', function(table) {
    table.uuid('id').primary().defaultTo(knex.raw('gen_random_uuid()'));
    table.uuid('item_id').notNullable();
    table.decimal('price', 15, 2).notNullable();
    table.string('region_id').notNullable().defaultTo('global');
    table.decimal('supply', 15, 2).defaultTo(0);
    table.decimal('demand', 15, 2).defaultTo(0);
    table.decimal('volatility', 5, 4).defaultTo(0);
    table.integer('transaction_count').defaultTo(0);
    table.decimal('volume_24h', 15, 2).defaultTo(0);
    table.json('metadata'); // Additional price data
    table.timestamp('created_at').defaultTo(knex.fn.now());

    // Foreign keys
    table.foreign('item_id').references('id').inTable('items').onDelete('CASCADE');

    // Indexes
    table.index(['item_id', 'region_id', 'created_at']);
    table.index(['region_id']);
    table.index(['created_at']);
    table.index(['price']);
  });
};

/**
 * @param { import("knex").Knex } knex
 * @returns { Promise<void> }
 */
exports.down = function(knex) {
  return knex.schema.dropTable('market_prices');
};