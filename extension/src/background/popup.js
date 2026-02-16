/**
 * WhatsApp Business Automation - Popup Script
 * Enhanced with subscription status, usage, and quick-send
 */

document.addEventListener('DOMContentLoaded', async () => {
  // DOM Elements
  const loginForm = document.getElementById('loginForm');
  const dashboard = document.getElementById('dashboard');
  const loginBtn = document.getElementById('loginBtn');
  const logoutBtn = document.getElementById('logoutBtn');
  const openDashboard = document.getElementById('openDashboard');
  const loginError = document.getElementById('loginError');

  // New elements for enhanced features
  const subscriptionBadge = document.getElementById('subscriptionBadge');
  const usageBar = document.getElementById('usageBar');
  const usageText = document.getElementById('usageText');
  const upgradeBanner = document.getElementById('upgradeBanner');
  const quickSendSection = document.getElementById('quickSendSection');
  const templatesSelect = document.getElementById('templatesSelect');
  const quickSendBtn = document.getElementById('quickSendBtn');
  const quickMessageInput = document.getElementById('quickMessageInput');
  const quickPhoneInput = document.getElementById('quickPhoneInput');
  const notificationsBtn = document.getElementById('notificationsBtn');
  const notificationsBadge = document.getElementById('notificationsBadge');

  // Check auth status
  const auth = await sendMessage({ type: 'GET_AUTH' });

  if (auth.authenticated) {
    showDashboard(auth.user, auth.subscription);
    await loadUsage();
    await loadTemplates();
    await checkAlerts();
  } else {
    showLogin();
  }

  // Login handler
  loginBtn.addEventListener('click', async () => {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    if (!username || !password) {
      showError('Please enter username and password');
      return;
    }

    loginBtn.disabled = true;
    loginBtn.textContent = 'Logging in...';

    try {
      const response = await sendMessage({
        type: 'LOGIN',
        data: { username, password }
      });

      if (response.success) {
        // Get subscription after login
        const subResponse = await sendMessage({ type: 'GET_SUBSCRIPTION' });
        showDashboard(response.user, subResponse.success ? subResponse.subscription : null);
        await loadUsage();
        await loadTemplates();
      } else {
        showError(response.error || 'Login failed');
      }
    } catch (error) {
      showError(error.message);
    } finally {
      loginBtn.disabled = false;
      loginBtn.textContent = 'Login';
    }
  });

  // Logout handler
  logoutBtn.addEventListener('click', async () => {
    await sendMessage({ type: 'LOGOUT' });
    showLogin();
  });

  // Open dashboard
  openDashboard.addEventListener('click', () => {
    sendMessage({ type: 'OPEN_DASHBOARD' });
  });

  // Quick send handler
  if (quickSendBtn) {
    quickSendBtn.addEventListener('click', async () => {
      const phone = quickPhoneInput.value.trim();
      const message = quickMessageInput.value.trim();
      const templateId = templatesSelect?.value;

      if (!phone && !templateId) {
        showQuickSendError('Please enter a phone number or select a template');
        return;
      }

      if (!message && !templateId) {
        showQuickSendError('Please enter a message or select a template');
        return;
      }

      quickSendBtn.disabled = true;
      quickSendBtn.textContent = 'Sending...';

      try {
        // Check limit first
        const checkResponse = await sendMessage({
          type: 'CHECK_LIMIT',
          data: { type: 'send_message' }
        });

        if (!checkResponse.canProceed) {
          showQuickSendError(checkResponse.reason);
          showUpgradeBanner();
          return;
        }

        // Prepare message data
        let messageContent = message;
        if (templateId && !message) {
          // Fetch template content
          const templates = await sendMessage({ type: 'GET_TEMPLATES' });
          const template = templates.templates.results.find(t => t.id == templateId);
          if (template) {
            messageContent = template.content;
          }
        }

        const response = await sendMessage({
          type: 'SEND_MESSAGE',
          data: {
            contact_phone: phone,
            message_content: messageContent,
            template_id: templateId
          }
        });

        if (response.success) {
          showQuickSendSuccess('Message sent successfully!');
          quickPhoneInput.value = '';
          quickMessageInput.value = '';
          if (templatesSelect) templatesSelect.value = '';

          // Update usage display
          await loadUsage();
        } else {
          showQuickSendError(response.error || 'Failed to send message');
        }
      } catch (error) {
        showQuickSendError(error.message);
      } finally {
        quickSendBtn.disabled = false;
        quickSendBtn.textContent = 'Send';
      }
    });
  }

  // Load templates into select
  async function loadTemplates() {
    if (!templatesSelect) return;

    try {
      const response = await sendMessage({ type: 'GET_TEMPLATES' });
      if (response.success && response.templates) {
        templatesSelect.innerHTML = '<option value="">Select a template...</option>';
        response.templates.results?.forEach(template => {
          const option = document.createElement('option');
          option.value = template.id;
          option.textContent = template.name;
          templatesSelect.appendChild(option);
        });
      }
    } catch (error) {
      console.error('Failed to load templates:', error);
    }
  }

  // Check for alerts
  async function checkAlerts() {
    try {
      const stats = await sendMessage({ type: 'GET_USER_STATS' });
      if (stats.success && stats.stats.alerts) {
        if (stats.stats.alerts.length > 0) {
          // Show notification badge
          if (notificationsBadge) {
            notificationsBadge.textContent = stats.stats.alerts.length;
            notificationsBadge.style.display = 'block';
          }
        }
      }
    } catch (error) {
      console.error('Failed to check alerts:', error);
    }
  }

  // Helper functions
  function sendMessage(message) {
    return new Promise((resolve) => {
      chrome.runtime.sendMessage(message, (response) => {
        resolve(response);
      });
    });
  }

  function showLogin() {
    loginForm.classList.add('active');
    dashboard.classList.remove('active');
    loginError.classList.remove('show');
  }

  function showDashboard(user, subscription) {
    loginForm.classList.remove('active');
    dashboard.classList.add('active');

    // Set user info
    document.getElementById('userName').textContent = user.user?.first_name
      ? `${user.user.first_name} ${user.user.last_name}`
      : user.user?.username || 'User';
    document.getElementById('userEmail').textContent = user.user?.email || '';
    document.getElementById('userAvatar').textContent = (user.user?.first_name || 'U')[0].toUpperCase();

    // Show subscription info
    if (subscriptionBadge && subscription) {
      const tier = subscription.plan?.tier || 'free';
      subscriptionBadge.textContent = tier.charAt(0).toUpperCase() + tier.slice(1);
      subscriptionBadge.className = `px-2 py-1 rounded text-xs font-semibold ${
        tier === 'enterprise' ? 'bg-purple-100 text-purple-800' :
        tier === 'pro' ? 'bg-blue-100 text-blue-800' :
        tier === 'starter' ? 'bg-green-100 text-green-800' :
        'bg-gray-100 text-gray-800'
      }`;
    }

    // Show quick send section
    if (quickSendSection) {
      quickSendSection.style.display = 'block';
    }
  }

  async function loadUsage() {
    try {
      const response = await sendMessage({ type: 'GET_USAGE' });

      if (response.success && response.usage) {
        const usage = response.usage;
        const percentage = usage.usage_percentage || 0;
        const remaining = usage.messages_remaining || 0;
        const limit = usage.message_limit || 0;

        if (usageBar) {
          usageBar.style.width = `${Math.min(percentage, 100)}%`;
          usageBar.className = `h-2 rounded-full transition-all ${
            percentage >= 90 ? 'bg-red-500' :
            percentage >= 75 ? 'bg-yellow-500' :
            'bg-green-500'
          }`;
        }

        if (usageText) {
          usageText.textContent = `${remaining} of ${limit} messages remaining`;
        }

        // Show upgrade banner if approaching limit
        if (percentage >= 80 && upgradeBanner) {
          showUpgradeBanner();
        }
      }
    } catch (error) {
      console.error('Failed to load usage:', error);
    }
  }

  function showUpgradeBanner() {
    if (upgradeBanner) {
      upgradeBanner.style.display = 'block';
    }
  }

  function showQuickSendError(message) {
    const errorEl = document.getElementById('quickSendError');
    if (errorEl) {
      errorEl.textContent = message;
      errorEl.style.display = 'block';
      setTimeout(() => {
        errorEl.style.display = 'none';
      }, 5000);
    }
  }

  function showQuickSendSuccess(message) {
    const successEl = document.getElementById('quickSendSuccess');
    if (successEl) {
      successEl.textContent = message;
      successEl.style.display = 'block';
      setTimeout(() => {
        successEl.style.display = 'none';
      }, 3000);
    }
  }

  function showError(message) {
    loginError.textContent = message;
    loginError.classList.add('show');
  }
});
