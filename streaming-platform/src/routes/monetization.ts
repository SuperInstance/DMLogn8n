import express from 'express';
import { MonetizationService } from '@/services/monetization';
import { DatabaseService } from '@/services/database';
import { logger } from '@/utils/logger';

const router = express.Router();

// Get subscription tiers
router.get('/subscriptions/tiers', async (req, res) => {
  try {
    const tiers = MonetizationService.getSubscriptionTiers();

    res.json({
      success: true,
      data: tiers
    });

  } catch (error) {
    logger.error('Failed to get subscription tiers:', error);
    res.status(500).json({ error: 'Failed to get subscription tiers', details: error.message });
  }
});

// Create subscription
router.post('/subscriptions/create', async (req, res) => {
  try {
    const { tierId, customerId } = req.body;

    if (!tierId || !customerId) {
      return res.status(400).json({ error: 'Tier ID and customer ID are required' });
    }

    const subscription = await MonetizationService.createSubscription(tierId, customerId);

    res.json({
      success: true,
      data: subscription
    });

  } catch (error) {
    logger.error('Failed to create subscription:', error);
    res.status(500).json({ error: 'Failed to create subscription', details: error.message });
  }
});

// Process donation
router.post('/donations/process', async (req, res) => {
  try {
    const donationData = {
      platform: req.body.platform,
      amount: req.body.amount,
      currency: req.body.currency || 'USD',
      donorName: req.body.donorName,
      message: req.body.message,
      email: req.body.email,
      isAnonymous: req.body.isAnonymous || false,
      sessionId: req.body.sessionId,
      rewardTier: req.body.rewardTier
    };

    const donation = await MonetizationService.processDonation(donationData);

    res.json({
      success: true,
      data: donation
    });

  } catch (error) {
    logger.error('Failed to process donation:', error);
    res.status(500).json({ error: 'Failed to process donation', details: error.message });
  }
});

// Get donations for session
router.get('/donations/session/:sessionId', async (req, res) => {
  try {
    const { sessionId } = req.params;

    const donations = await DatabaseService.getDonationsBySession(sessionId);

    res.json({
      success: true,
      data: donations
    });

  } catch (error) {
    logger.error('Failed to get session donations:', error);
    res.status(500).json({ error: 'Failed to get session donations', details: error.message });
  }
});

// Create Stripe payment intent
router.post('/payments/stripe/create-intent', async (req, res) => {
  try {
    const { amount, currency } = req.body;

    if (!amount || amount <= 0) {
      return res.status(400).json({ error: 'Valid amount is required' });
    }

    const paymentIntent = await MonetizationService.createStripePaymentIntent(amount, currency);

    res.json({
      success: true,
      data: paymentIntent
    });

  } catch (error) {
    logger.error('Failed to create Stripe payment intent:', error);
    res.status(500).json({ error: 'Failed to create payment intent', details: error.message });
  }
});

// Create PayPal payment
router.post('/payments/paypal/create', async (req, res) => {
  try {
    const { amount, currency } = req.body;

    if (!amount || amount <= 0) {
      return res.status(400).json({ error: 'Valid amount is required' });
    }

    const payment = await MonetizationService.createPayPalPayment(amount, currency);

    res.json({
      success: true,
      data: payment
    });

  } catch (error) {
    logger.error('Failed to create PayPal payment:', error);
    res.status(500).json({ error: 'Failed to create PayPal payment', details: error.message });
  }
});

// Get merchandise items
router.get('/merchandise', async (req, res) => {
  try {
    const items = MonetizationService.getMerchandiseItems();

    res.json({
      success: true,
      data: items
    });

  } catch (error) {
    logger.error('Failed to get merchandise:', error);
    res.status(500).json({ error: 'Failed to get merchandise', details: error.message });
  }
});

// Purchase merchandise
router.post('/merchandise/purchase', async (req, res) => {
  try {
    const { itemId, quantity, customerInfo } = req.body;

    if (!itemId || !quantity || !customerInfo) {
      return res.status(400).json({ error: 'Item ID, quantity, and customer info are required' });
    }

    const purchase = await MonetizationService.purchaseMerchandise(itemId, quantity, customerInfo);

    res.json({
      success: true,
      data: purchase
    });

  } catch (error) {
    logger.error('Failed to purchase merchandise:', error);
    res.status(500).json({ error: 'Failed to purchase merchandise', details: error.message });
  }
});

// Get sponsorship tiers
router.get('/sponsorships/tiers', async (req, res) => {
  try {
    const tiers = MonetizationService.getSponsorshipTiers();

    res.json({
      success: true,
      data: tiers
    });

  } catch (error) {
    logger.error('Failed to get sponsorship tiers:', error);
    res.status(500).json({ error: 'Failed to get sponsorship tiers', details: error.message });
  }
});

// Purchase sponsorship
router.post('/sponsorships/purchase', async (req, res) => {
  try {
    const { tierId, sponsorInfo } = req.body;

    if (!tierId || !sponsorInfo) {
      return res.status(400).json({ error: 'Tier ID and sponsor info are required' });
    }

    const sponsorship = await MonetizationService.purchaseSponsorship(tierId, sponsorInfo);

    res.json({
      success: true,
      data: sponsorship
    });

  } catch (error) {
    logger.error('Failed to purchase sponsorship:', error);
    res.status(500).json({ error: 'Failed to purchase sponsorship', details: error.message });
  }
});

// Revenue analytics
router.get('/analytics/revenue', async (req, res) => {
  try {
    const { startDate, endDate } = req.query;

    if (!startDate || !endDate) {
      return res.status(400).json({ error: 'Start date and end date are required' });
    }

    const revenueBreakdown = await MonetizationService.getRevenueBreakdown(
      new Date(startDate as string),
      new Date(endDate as string)
    );

    res.json({
      success: true,
      data: revenueBreakdown
    });

  } catch (error) {
    logger.error('Failed to get revenue analytics:', error);
    res.status(500).json({ error: 'Failed to get revenue analytics', details: error.message });
  }
});

// Webhook handlers
router.post('/webhooks/stripe', express.raw({ type: 'application/json' }), async (req, res) => {
  try {
    const sig = req.headers['stripe-signature'];
    const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);

    let event;

    try {
      event = stripe.webhooks.constructEvent(req.body, sig!, process.env.STRIPE_WEBHOOK_SECRET!);
    } catch (err: any) {
      logger.error('Stripe webhook signature verification failed:', err.message);
      return res.status(400).send(`Webhook Error: ${err.message}`);
    }

    await MonetizationService.handleStripeWebhook(event);

    res.json({ received: true });

  } catch (error) {
    logger.error('Failed to handle Stripe webhook:', error);
    res.status(500).json({ error: 'Failed to handle webhook', details: error.message });
  }
});

router.post('/webhooks/paypal', async (req, res) => {
  try {
    // Handle PayPal webhook
    const { event_type, resource } = req.body;

    logger.info(`PayPal webhook received: ${event_type}`);

    // Process different webhook types
    switch (event_type) {
      case 'PAYMENT.SALE.COMPLETED':
        // Handle successful payment
        logger.info('PayPal payment completed:', resource.id);
        break;
      case 'PAYMENT.SALE.DENIED':
        // Handle denied payment
        logger.warn('PayPal payment denied:', resource.id);
        break;
      default:
        logger.info(`Unhandled PayPal webhook type: ${event_type}`);
    }

    res.json({ received: true });

  } catch (error) {
    logger.error('Failed to handle PayPal webhook:', error);
    res.status(500).json({ error: 'Failed to handle webhook', details: error.message });
  }
});

// Top donors
router.get('/donors/top', async (req, res) => {
  try {
    const { limit = 10, period = 'all' } = req.query;

    // This would query the database for top donors
    // For now, return placeholder data
    const topDonors = [
      { name: 'DragonSlayer99', total: 250, donations: 5 },
      { name: 'DiceMaster', total: 180, donations: 3 },
      { name: 'WizardFan', total: 150, donations: 4 }
    ];

    res.json({
      success: true,
      data: topDonors
    });

  } catch (error) {
    logger.error('Failed to get top donors:', error);
    res.status(500).json({ error: 'Failed to get top donors', details: error.message });
  }
});

// Subscription statistics
router.get('/subscriptions/stats', async (req, res) => {
  try {
    // This would query the database for subscription statistics
    const stats = {
      totalSubscribers: 125,
      newThisMonth: 15,
      churnRate: 0.05,
      revenuePerMonth: 1875,
      topTier: 'gold',
      tierBreakdown: {
        bronze: 75,
        silver: 35,
        gold: 15
      }
    };

    res.json({
      success: true,
      data: stats
    });

  } catch (error) {
    logger.error('Failed to get subscription stats:', error);
    res.status(500).json({ error: 'Failed to get subscription stats', details: error.message });
  }
});

export default router;