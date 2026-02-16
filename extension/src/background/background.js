/**
 * WhatsApp Business Automation - Background Service Worker
 * Enhanced with JWT auth, subscription enforcement, and rate limiting
 */

// API Configuration
const API_URL = process.env.API_URL || 'http://localhost:8000/api/v1';

// Storage keys
const STORAGE_KEYS = {
  AUTH_TOKEN: 'auth_token',
  REFRESH_TOKEN: 'refresh_token',
  USER: 'user',
  SUBSCRIPTION: 'subscription',
  USAGE: 'usage',
  TEMPLATES: 'templates',
  SETTINGS: 'settings',
};

// Rate limiting configuration
const RATE_LIMITS = {
  free: { messagesPerDay: 100, requestsPerMinute: 10 },
  starter: { messagesPerDay: 1000, requestsPerMinute: 30 },
  pro: { messagesPerDay: 10000, requestsPerMinute: 100 },
  enterprise: { messagesPerDay: 50000, requestsPerMinute: 300 },
};

// Listen for messages from content script and popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('Background received message:', message.type);

  switch (message.type) {
    case 'GET_AUTH':
      handleGetAuth(sendResponse);
      return true;

    case 'LOGIN':
      handleLogin(message.data, sendResponse);
      return true;

    case 'LOGOUT':
      handleLogout(sendResponse);
      return true;

    case 'GET_SUBSCRIPTION':
      handleGetSubscription(sendResponse);
      return true;

    case 'GET_USAGE':
      handleGetUsage(sendResponse);
      return true;

    case 'CHECK_LIMIT':
      handleCheckLimit(message.data, sendResponse);
      return true;

    case 'GET_CONTACTS':
      handleGetContacts(message.data, sendResponse);
      return true;

    case 'GET_TEMPLATES':
      handleGetTemplates(sendResponse);
      return true;

    case 'SEND_MESSAGE':
      handleSendMessage(message.data, sendResponse);
      return true;

    case 'SCHEDULE_MESSAGE':
      handleScheduleMessage(message.data, sendResponse);
      return true;

    case 'SAVE_CONTACT':
      handleSaveContact(message.data, sendResponse);
      return true;

    case 'GET_USER_STATS':
      handleGetUserStats(sendResponse);
      return true;

    case 'REFRESH_TOKEN':
      handleRefreshToken(sendResponse);
      return true;

    case 'OPEN_DASHBOARD':
      handleOpenDashboard(sendResponse);
      return true;

    case 'GET_NOTIFICATIONS':
      handleGetNotifications(sendResponse);
      return true;

    default:
      sendResponse({ success: false, error: 'Unknown message type' });
  }
});

/**
 * Get authentication status
 */
async function handleGetAuth(sendResponse) {
  try {
    const authToken = await chrome.storage.local.get(STORAGE_KEYS.AUTH_TOKEN);
    const user = await chrome.storage.local.get(STORAGE_KEYS.USER);
    const subscription = await chrome.storage.local.get(STORAGE_KEYS.SUBSCRIPTION);

    if (authToken[STORAGE_KEYS.AUTH_TOKEN]) {
      sendResponse({
        success: true,
        authenticated: true,
        user: user[STORAGE_KEYS.USER],
        subscription: subscription[STORAGE_KEYS.SUBSCRIPTION] || null
      });
    } else {
      sendResponse({ success: true, authenticated: false });
    }
  } catch (error) {
    console.error('Get auth error:', error);
    sendResponse({ success: false, error: error.message });
  }
}

/**
 * Handle login request
 */
async function handleLogin(data, sendResponse) {
  try {
    const response = await fetch(`${API_URL}/auth/login/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.non_field_errors?.[0] || 'Login failed');
    }

    const tokens = await response.json();

    // Store tokens
    await chrome.storage.local.set({
      [STORAGE_KEYS.AUTH_TOKEN]: tokens.access,
      [STORAGE_KEYS.REFRESH_TOKEN]: tokens.refresh,
      [STORAGE_KEYS.USER]: tokens.user,
    });

    // Fetch subscription details
    try {
      const subResponse = await fetch(`${API_URL}/billing/subscription/`, {
        headers: {
          'Authorization': `Bearer ${tokens.access}`,
        },
      });
      if (subResponse.ok) {
        const subscription = await subResponse.json();
        await chrome.storage.local.set({
          [STORAGE_KEYS.SUBSCRIPTION]: subscription,
        });
      }
    } catch (e) {
      console.error('Failed to fetch subscription:', e);
    }

    sendResponse({ success: true, user: tokens.user });
  } catch (error) {
    console.error('Login error:', error);
    sendResponse({ success: false, error: error.message });
  }
}

/**
 * Handle logout request
 */
async function handleLogout(sendResponse) {
  try {
    const refreshToken = await chrome.storage.local.get(STORAGE_KEYS.REFRESH_TOKEN);

    if (refreshToken[STORAGE_KEYS.REFRESH_TOKEN]) {
      try {
        await fetch(`${API_URL}/auth/logout/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${await getAuthToken()}`,
          },
          body: JSON.stringify({ refresh: refreshToken[STORAGE_KEYS.REFRESH_TOKEN] }),
        });
      } catch (e) {
        // Ignore logout API errors
      }
    }

    // Clear storage
    await chrome.storage.local.remove([
      STORAGE_KEYS.AUTH_TOKEN,
      STORAGE_KEYS.REFRESH_TOKEN,
      STORAGE_KEYS.USER,
      STORAGE_KEYS.SUBSCRIPTION,
      STORAGE_KEYS.USAGE,
      STORAGE_KEYS.TEMPLATES,
    ]);

    sendResponse({ success: true });
  } catch (error) {
    console.error('Logout error:', error);
    sendResponse({ success: false, error: error.message });
  }
}

/**
 * Get subscription details
 */
async function handleGetSubscription(sendResponse) {
  try {
    const token = await getAuthToken();

    const response = await fetch(`${API_URL}/billing/subscription/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch subscription');
    }

    const subscription = await response.json();

    // Cache subscription
    await chrome.storage.local.set({
      [STORAGE_KEYS.SUBSCRIPTION]: subscription,
    });

    sendResponse({ success: true, subscription });
  } catch (error) {
    console.error('Get subscription error:', error);
    sendResponse({ success: false, error: error.message });
  }
}

/**
 * Get usage statistics
 */
async function handleGetUsage(sendResponse) {
  try {
    const token = await getAuthToken();

    const response = await fetch(`${API_URL}/billing/usage/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch usage');
    }

    const usage = await response.json();

    // Cache usage
    await chrome.storage.local.set({
      [STORAGE_KEYS.USAGE]: usage,
    });

    sendResponse({ success: true, usage });
  } catch (error) {
    console.error('Get usage error:', error);
    sendResponse({ success: false, error: error.message });
  }
}

/**
 * Check if user can send message (rate limiting)
 */
async function handleCheckLimit(data, sendResponse) {
  try {
    const { type } = data;
    const subscription = await chrome.storage.local.get(STORAGE_KEYS.SUBSCRIPTION);
    const usage = await chrome.storage.local.get(STORAGE_KEYS.USAGE);

    const sub = subscription[STORAGE_KEYS.SUBSCRIPTION];
    const use = usage[STORAGE_KEYS.USAGE];

    if (!sub) {
      sendResponse({
        success: false,
        canProceed: false,
        reason: 'No subscription found',
        upgradeUrl: '/dashboard/billing'
      });
      return;
    }

    const tier = sub.plan?.tier || 'free';
    const limits = RATE_LIMITS[tier] || RATE_LIMITS.free;

    // Check daily message limit
    if (type === 'send_message') {
      if (use) {
        const messagesRemaining = use.messages_remaining || 0;
        if (messagesRemaining <= 0) {
          sendResponse({
            success: false,
            canProceed: false,
            reason: 'Daily message limit reached',
            upgradeUrl: '/dashboard/billing/upgrade'
          });
          return;
        }
      }

      // Check if approaching limit (80%)
      if (use && use.usage_percentage >= 80) {
        sendResponse({
          success: true,
          canProceed: true,
          warning: `Approaching limit: ${use.usage_percentage}% used`,
          upgradeUrl: '/dashboard/billing/upgrade'
        });
        return;
      }
    }

    sendResponse({ success: true, canProceed: true });
  } catch (error) {
    console.error('Check limit error:', error);
    // Allow on error, but log
    sendResponse({ success: true, canProceed: true });
  }
}

/**
 * Get contacts from API
 */
async function handleGetContacts(data, sendResponse) {
  try {
    const token = await getAuthToken();
    const params = new URLSearchParams(data || {});

    const response = await fetch(`${API_URL}/contacts/?${params}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch contacts');
    }

    const contacts = await response.json();
    sendResponse({ success: true, contacts });
  } catch (error) {
    console.error('Get contacts error:', error);
    sendResponse({ success: false, error: error.message });
  }
}

/**
 * Get templates from API
 */
async function handleGetTemplates(sendResponse) {
  try {
    const token = await getAuthToken();

    const response = await fetch(`${API_URL}/templates/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch templates');
    }

    const templates = await response.json();

    // Cache templates
    await chrome.storage.local.set({
      [STORAGE_KEYS.TEMPLATES]: templates,
    });

    sendResponse({ success: true, templates });
  } catch (error) {
    console.error('Get templates error:', error);

    // Try to get from cache
    const cached = await chrome.storage.local.get(STORAGE_KEYS.TEMPLATES);
    if (cached[STORAGE_KEYS.TEMPLATES]) {
      sendResponse({ success: true, templates: cached[STORAGE_KEYS.TEMPLATES] });
    } else {
      sendResponse({ success: false, error: error.message });
    }
  }
}

/**
 * Save contact to API
 */
async function handleSaveContact(data, sendResponse) {
  try {
    const token = await getAuthToken();

    const response = await fetch(`${API_URL}/contacts/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(JSON.stringify(error));
    }

    const contact = await response.json();
    sendResponse({ success: true, contact });
  } catch (error) {
    console.error('Save contact error:', error);
    sendResponse({ success: false, error: error.message });
  }
}

/**
 * Send message via API
 */
async function handleSendMessage(data, sendResponse) {
  try {
    // First check rate limits
    const checkResponse = await new Promise((resolve) => {
      handleCheckLimit({ type: 'send_message' }, resolve);
    });

    if (!checkResponse.canProceed) {
      sendResponse({
        success: false,
        error: checkResponse.reason,
        upgradeUrl: checkResponse.upgradeUrl,
        rateLimited: true
      });
      return;
    }

    const token = await getAuthToken();

    const response = await fetch(`${API_URL}/messages/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(JSON.stringify(error));
    }

    const message = await response.json();

    // Update cached usage
    await updateUsageCache();

    sendResponse({ success: true, message, warning: checkResponse.warning });
  } catch (error) {
    console.error('Send message error:', error);
    sendResponse({ success: false, error: error.message });
  }
}

/**
 * Schedule message via API
 */
async function handleScheduleMessage(data, sendResponse) {
  try {
    const token = await getAuthToken();

    const response = await fetch(`${API_URL}/scheduled/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(JSON.stringify(error));
    }

    const scheduled = await response.json();
    sendResponse({ success: true, scheduled });
  } catch (error) {
    console.error('Schedule message error:', error);
    sendResponse({ success: false, error: error.message });
  }
}

/**
 * Get user stats
 */
async function handleGetUserStats(sendResponse) {
  try {
    const token = await getAuthToken();

    const response = await fetch(`${API_URL}/billing/stats/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch stats');
    }

    const stats = await response.json();
    sendResponse({ success: true, stats });
  } catch (error) {
    console.error('Get stats error:', error);
    sendResponse({ success: false, error: error.message });
  }
}

/**
 * Get notifications
 */
async function handleGetNotifications(sendResponse) {
  try {
    const token = await getAuthToken();

    const response = await fetch(`${API_URL}/notifications/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch notifications');
    }

    const notifications = await response.json();
    sendResponse({ success: true, notifications });
  } catch (error) {
    console.error('Get notifications error:', error);
    sendResponse({ success: false, error: error.message });
  }
}

/**
 * Refresh auth token
 */
async function handleRefreshToken(sendResponse) {
  try {
    const newToken = await refreshAuthToken();
    sendResponse({ success: true, token: newToken });
  } catch (error) {
    console.error('Token refresh error:', error);
    sendResponse({ success: false, error: error.message });
  }
}

/**
 * Open dashboard
 */
async function handleOpenDashboard(sendResponse) {
  const dashboardUrl = process.env.DASHBOARD_URL || 'http://localhost:3000/dashboard';
  chrome.tabs.create({ url: dashboardUrl });
  sendResponse({ success: true });
}

/**
 * Get auth token from storage
 */
async function getAuthToken() {
  const result = await chrome.storage.local.get(STORAGE_KEYS.AUTH_TOKEN);
  return result[STORAGE_KEYS.AUTH_TOKEN];
}

/**
 * Refresh auth token
 */
async function refreshAuthToken() {
  try {
    const refreshToken = await chrome.storage.local.get(STORAGE_KEYS.REFRESH_TOKEN);

    if (!refreshToken[STORAGE_KEYS.REFRESH_TOKEN]) {
      throw new Error('No refresh token');
    }

    const response = await fetch(`${API_URL}/auth/token/refresh/custom/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh: refreshToken[STORAGE_KEYS.REFRESH_TOKEN] }),
    });

    if (!response.ok) {
      throw new Error('Token refresh failed');
    }

    const tokens = await response.json();

    await chrome.storage.local.set({
      [STORAGE_KEYS.AUTH_TOKEN]: tokens.access,
      [STORAGE_KEYS.REFRESH_TOKEN]: tokens.refresh,
    });

    return tokens.access;
  } catch (error) {
    console.error('Token refresh error:', error);
    await chrome.storage.local.remove([
      STORAGE_KEYS.AUTH_TOKEN,
      STORAGE_KEYS.REFRESH_TOKEN,
      STORAGE_KEYS.USER,
    ]);
    throw error;
  }
}

/**
 * Update usage cache
 */
async function updateUsageCache() {
  try {
    const token = await getAuthToken();
    const response = await fetch(`${API_URL}/billing/usage/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    if (response.ok) {
      const usage = await response.json();
      await chrome.storage.local.set({ [STORAGE_KEYS.USAGE]: usage });
    }
  } catch (error) {
    console.error('Failed to update usage cache:', error);
  }
}

/**
 * Periodic usage check (every 5 minutes)
 */
setInterval(async () => {
  const auth = await chrome.storage.local.get(STORAGE_KEYS.AUTH_TOKEN);
  if (auth[STORAGE_KEYS.AUTH_TOKEN]) {
    await updateUsageCache();
  }
}, 5 * 60 * 1000);

// Handle extension installation
chrome.runtime.onInstalled.addListener((details) => {
  console.log('Extension installed:', details.reason);

  if (details.reason === 'install') {
    // First time installation
    console.log('WhatsApp Business Automation extension installed');
  }
});

// Handle extension update
chrome.runtime.onUpdateAvailable.addListener(() => {
  console.log('Extension update available');
});
