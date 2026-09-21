/**
 * @param { import("knex").Knex } knex
 * @returns { Promise<void> }
 */
exports.up = function(knex) {
  // Players table
  return knex.schema.createTable('players', function(table) {
    table.uuid('id').primary().defaultTo(knex.raw('gen_random_uuid()'));
    table.string('username').notNullable().unique();
    table.string('email').unique();
    table.string('display_name');
    table.string('avatar');
    table.enum('status', ['active', 'inactive', 'banned']).defaultTo('active');
    table.timestamp('last_login');
    table.timestamp('created_at').defaultTo(knex.fn.now());
    table.timestamp('updated_at').defaultTo(knex.fn.now());

    table.index(['username']);
    table.index(['status']);
    table.index(['last_login']);
  })
  .then(() => {
    // Player reputation table
    return knex.schema.createTable('player_reputation', function(table) {
      table.uuid('player_id').primary();
      table.decimal('reputation', 10, 2).defaultTo(0);
      table.integer('total_actions').defaultTo(0);
      table.integer('successful_trades').defaultTo(0);
      table.integer('failed_trades').defaultTo(0);
      table.decimal('total_volume', 15, 2).defaultTo(0);
      table.timestamp('created_at').defaultTo(knex.fn.now());
      table.timestamp('updated_at').defaultTo(knex.fn.now());

      table.foreign('player_id').references('id').inTable('players').onDelete('CASCADE');
      table.index(['reputation']);
    });
  })
  .then(() => {
    // Price alerts table
    return knex.schema.createTable('price_alerts', function(table) {
      table.uuid('id').primary().defaultTo(knex.raw('gen_random_uuid()'));
      table.uuid('player_id').notNullable();
      table.uuid('item_id').notNullable();
      table.string('region_id').notNullable().defaultTo('global');
      table.enum('alert_type', ['above', 'below', 'percentage_change']).notNullable();
      table.decimal('threshold', 15, 2).notNullable();
      table.enum('status', ['active', 'triggered', 'expired', 'cancelled']).defaultTo('active');
      table.enum('notification_method', ['in_game', 'email', 'push']).defaultTo('in_game');
      table.timestamp('created_at').defaultTo(knex.fn.now());
      table.timestamp('expires_at');
      table.timestamp('triggered_at');
      table.decimal('triggered_price', 15, 2);

      table.foreign('player_id').references('id').inTable('players').onDelete('CASCADE');
      table.foreign('item_id').references('id').inTable('items').onDelete('CASCADE');
      table.index(['player_id', 'status']);
      table.index(['item_id', 'region_id']);
      table.index(['status']);
    });
  })
  .then(() => {
    // Trade requests table
    return knex.schema.createTable('trade_requests', function(table) {
      table.uuid('id').primary().defaultTo(knex.raw('gen_random_uuid()'));
      table.uuid('requester_id').notNullable();
      table.uuid('target_id').notNullable();
      table.json('requester_items'); // Items offered by requester
      table.json('target_items'); // Items requested from target
      table.decimal('requester_currency', 15, 2); // Currency offered
      table.decimal('target_currency', 15, 2); // Currency requested
      table.text('message');
      table.enum('status', ['pending', 'accepted', 'rejected', 'expired', 'cancelled']).defaultTo('pending');
      table.timestamp('created_at').defaultTo(knex.fn.now());
      table.timestamp('updated_at').defaultTo(knex.fn.now());
      table.timestamp('expires_at');
      table.timestamp('completed_at');

      table.foreign('requester_id').references('id').inTable('players').onDelete('CASCADE');
      table.foreign('target_id').references('id').inTable('players').onDelete('CASCADE');
      table.index(['requester_id', 'status']);
      table.index(['target_id', 'status']);
      table.index(['status']);
      table.index(['expires_at']);
    });
  })
  .then(() => {
    // Regional events table
    return knex.schema.createTable('regional_events', function(table) {
      table.uuid('id').primary().defaultTo(knex.raw('gen_random_uuid()'));
      table.string('region_id').notNullable();
      table.string('name').notNullable();
      table.text('description');
      table.enum('type', ['prosperity', 'shortage', 'war', 'festival', 'disaster']).notNullable();
      table.decimal('impact', 5, 3).notNullable(); // Multiplier for prices/supply
      table.boolean('active').defaultTo(true);
      table.timestamp('starts_at').notNullable();
      table.timestamp('ends_at').notNullable();
      table.json('effects'); // Specific effects on items/categories
      table.timestamp('created_at').defaultTo(knex.fn.now());

      table.index(['region_id']);
      table.index(['type']);
      table.index(['active']);
      table.index(['starts_at']);
      table.index(['ends_at']);
    });
  })
  .then(() => {
    // Market analytics cache table
    return knex.schema.createTable('market_analytics_cache', function(table) {
      table.uuid('id').primary().defaultTo(knex.raw('gen_random_uuid()'));
      table.string('cache_key').notNullable().unique();
      table.string('region_id').notNullable();
      table.string('analysis_type').notNullable(); // 'trends', 'opportunities', 'risks', etc.
      table.json('data').notNullable();
      table.timestamp('expires_at').notNullable();
      table.timestamp('created_at').defaultTo(knex.fn.now());

      table.index(['cache_key']);
      table.index(['region_id']);
      table.index(['analysis_type']);
      table.index(['expires_at']);
    });
  });
};

/**
 * @param { import("knex").Knex } knex
 * @returns { Promise<void> }
 */
exports.down = function(knex) {
  return knex.schema.dropTableIfExists('market_analytics_cache')
    .then(() => knex.schema.dropTableIfExists('regional_events'))
    .then(() => knex.schema.dropTableIfExists('trade_requests'))
    .then(() => knex.schema.dropTableIfExists('price_alerts'))
    .then(() => knex.schema.dropTableIfExists('player_reputation'))
    .then(() => knex.schema.dropTableIfExists('players'));
};