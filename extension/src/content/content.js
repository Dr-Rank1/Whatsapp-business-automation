/**
 * WhatsApp Business Automation - Content Script
 * Injected into web.whatsapp.com
 */

(function() {
  'use strict';

  console.log('WhatsApp Business Automation: Content script loaded');

  // Configuration
  const CONFIG = {
    checkInterval: 1000,
    maxRetries: 10,
  };

  // State
  let isInitialized = false;
  let currentChatPhone = null;
  let authToken = null;

  /**
   * Initialize the extension
   */
  async function init() {
    if (isInitialized) return;
    
    console.log('Initializing WhatsApp Automation...');
    
    // Check authentication
    const auth = await sendMessage({ type: 'GET_AUTH' });
    
    if (!auth.authenticated) {
      console.log('User not authenticated');
      showLoginPrompt();
      return;
    }
    
    console.log('User authenticated:', auth.user);
    authToken = auth.token;
    
    // Wait for WhatsApp to load
    await waitForWhatsApp();
    
    // Inject UI
    injectUI();
    
    // Set up observers
    setupObservers();
    
    isInitialized = true;
    console.log('WhatsApp Automation initialized');
  }

  /**
   * Send message to background script
   */
  function sendMessage(message) {
    return new Promise((resolve) => {
      chrome.runtime.sendMessage(message, (response) => {
        resolve(response);
      });
    });
  }

  /**
   * Wait for WhatsApp to fully load
   */
  async function waitForWhatsApp() {
    let retries = 0;
    
    while (retries < CONFIG.maxRetries) {
      const app = document.querySelector('#app');
      const conversation = document.querySelector('[data-testid="conversation-panel"]');
      
      if (app && conversation) {
        console.log('WhatsApp loaded');
        return true;
      }
      
      await new Promise(resolve => setTimeout(resolve, CONFIG.checkInterval));
      retries++;
    }
    
    throw new Error('WhatsApp failed to load');
  }

  /**
   * Show login prompt
   */
  function showLoginPrompt() {
    const banner = document.createElement('div');
    banner.id = 'wa-automation-login-banner';
    banner.innerHTML = `
      <div class="wa-automation-banner">
        <span>Please login to WhatsApp Business Automation</span>
        <a href="#" id="wa-automation-open-popup">Open Extension</a>
      </div>
    `;
    document.body.appendChild(banner);
    
    document.getElementById('wa-automation-open-popup').addEventListener('click', (e) => {
      e.preventDefault();
      chrome.runtime.sendMessage({ type: 'OPEN_POPUP' });
    });
  }

  /**
   * Inject UI elements
   */
  function injectUI() {
    // Inject styles
    injectStyles();
    
    // Create floating button
    createFloatingButton();
    
    // Add panel container
    createPanelContainer();
  }

  /**
   * Inject CSS styles
   */
  function injectStyles() {
    const styles = `
      .wa-automation-banner {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        background: #dc2626;
        color: white;
        padding: 12px 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        z-index: 10000;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      }
      
      .wa-automation-banner a {
        color: white;
        text-decoration: underline;
      }
      
      .wa-automation-fab {
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 56px;
        height: 56px;
        border-radius: 50%;
        background: #25D366;
        color: white;
        border: none;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 9999;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: transform 0.2s, background 0.2s;
      }
      
      .wa-automation-fab:hover {
        transform: scale(1.1);
        background: #128C7E;
      }
      
      .wa-automation-fab svg {
        width: 24px;
        height: 24px;
      }
      
      .wa-automation-panel {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 400px;
        max-height: 80vh;
        background: white;
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        z-index: 10000;
        overflow: hidden;
        display: none;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      }
      
      .wa-automation-panel.open {
        display: block;
      }
      
      .wa-automation-panel-header {
        background: #128C7E;
        color: white;
        padding: 16px 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      
      .wa-automation-panel-header h2 {
        margin: 0;
        font-size: 18px;
      }
      
      .wa-automation-panel-close {
        background: none;
        border: none;
        color: white;
        cursor: pointer;
        font-size: 24px;
        line-height: 1;
      }
      
      .wa-automation-panel-content {
        padding: 20px;
        max-height: calc(80vh - 60px);
        overflow-y: auto;
      }
      
      .wa-automation-form-group {
        margin-bottom: 16px;
      }
      
      .wa-automation-form-group label {
        display: block;
        margin-bottom: 6px;
        font-weight: 500;
        color: #333;
      }
      
      .wa-automation-form-group input,
      .wa-automation-form-group textarea,
      .wa-automation-form-group select {
        width: 100%;
        padding: 10px 12px;
        border: 1px solid #ddd;
        border-radius: 8px;
        font-size: 14px;
        box-sizing: border-box;
      }
      
      .wa-automation-form-group textarea {
        min-height: 100px;
        resize: vertical;
      }
      
      .wa-automation-btn {
        padding: 10px 20px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        border: none;
        transition: background 0.2s;
      }
      
      .wa-automation-btn-primary {
        background: #25D366;
        color: white;
        width: 100%;
      }
      
      .wa-automation-btn-primary:hover {
        background: #128C7E;
      }
      
      .wa-automation-btn-secondary {
        background: #f0f0f0;
        color: #333;
        margin-right: 8px;
      }
      
      .wa-automation-contacts-list {
        max-height: 200px;
        overflow-y: auto;
        border: 1px solid #ddd;
        border-radius: 8px;
      }
      
      .wa-automation-contact-item {
        padding: 10px 12px;
        cursor: pointer;
        border-bottom: 1px solid #f0f0f0;
        display: flex;
        justify-content: space-between;
      }
      
      .wa-automation-contact-item:hover {
        background: #f5f5f5;
      }
      
      .wa-automation-contact-item.selected {
        background: #e8f5e9;
      }
      
      .wa-automation-message {
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 8px;
      }
      
      .wa-automation-message.success {
        background: #e8f5e9;
        color: #2e7d32;
      }
      
      .wa-automation-message.error {
        background: #ffebee;
        color: #c62828;
      }
    `;
    
    const styleElement = document.createElement('style');
    styleElement.textContent = styles;
    document.head.appendChild(styleElement);
  }

  /**
   * Create floating action button
   */
  function createFloatingButton() {
    const fab = document.createElement('button');
    fab.className = 'wa-automation-fab';
    fab.innerHTML = `
      <svg viewBox="0 0 24 24" fill="currentColor">
        <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.17L4 17.17V4h16v12z"/>
        <path d="M7 9h10v2H7zm0-3h10v2H7z"/>
      </svg>
    `;
    fab.title = 'WhatsApp Automation';
    fab.addEventListener('click', togglePanel);
    document.body.appendChild(fab);
  }

  /**
   * Create panel container
   */
  function createPanelContainer() {
    const panel = document.createElement('div');
    panel.className = 'wa-automation-panel';
    panel.id = 'wa-automation-panel';
    panel.innerHTML = `
      <div class="wa-automation-panel-header">
        <h2>WhatsApp Automation</h2>
        <button class="wa-automation-panel-close">&times;</button>
      </div>
      <div class="wa-automation-panel-content">
        <!-- Content will be populated dynamically -->
      </div>
    `;
    
    panel.querySelector('.wa-automation-panel-close').addEventListener('click', closePanel);
    document.body.appendChild(panel);
  }

  /**
   * Toggle panel
   */
  function togglePanel() {
    const panel = document.getElementById('wa-automation-panel');
    panel.classList.toggle('open');
    
    if (panel.classList.contains('open')) {
      loadTemplates();
      loadContacts();
    }
  }

  /**
   * Close panel
   */
  function closePanel() {
    const panel = document.getElementById('wa-automation-panel');
    panel.classList.remove('open');
  }

  /**
   * Load templates
   */
  async function loadTemplates() {
    const response = await sendMessage({ type: 'GET_TEMPLATES' });
    
    if (response.success) {
      renderTemplates(response.templates.results || response.templates);
    }
  }

  /**
   * Load contacts
   */
  async function loadContacts() {
    const response = await sendMessage({ type: 'GET_CONTACTS' });
    
    if (response.success) {
      renderContacts(response.contacts.results || response.contacts);
    }
  }

  /**
   * Render templates
   */
  function renderTemplates(templates) {
    const content = document.querySelector('.wa-automation-panel-content');
    const templateOptions = templates.map(t => 
      `<option value="${t.id}">${t.name}</option>`
    ).join('');
    
    content.innerHTML = `
      <div class="wa-automation-form-group">
        <label>Send Quick Message</label>
        <select id="wa-template-select">
          <option value="">Select a template...</option>
          ${templateOptions}
        </select>
      </div>
      <div class="wa-automation-form-group">
        <label>Or type a custom message</label>
        <textarea id="wa-custom-message" placeholder="Type your message..."></textarea>
      </div>
      <div class="wa-automation-form-group">
        <label>Or select a contact</label>
        <div class="wa-automation-contacts-list" id="wa-contacts-list">
          <div style="padding: 12px; color: #666;">Loading contacts...</div>
        </div>
      </div>
      <button class="wa-automation-btn wa-automation-btn-primary" id="wa-send-btn">
        Send Message
      </button>
    `;
    
    // Set up event listeners
    document.getElementById('wa-template-select').addEventListener('change', (e) => {
      const template = templates.find(t => t.id === parseInt(e.target.value));
      if (template) {
        document.getElementById('wa-custom-message').value = template.content;
      }
    });
    
    document.getElementById('wa-send-btn').addEventListener('click', sendQuickMessage);
  }

  /**
   * Render contacts
   */
  function renderContacts(contacts) {
    const list = document.getElementById('wa-contacts-list');
    if (!list) return;
    
    if (contacts.length === 0) {
      list.innerHTML = '<div style="padding: 12px; color: #666;">No contacts found</div>';
      return;
    }
    
    list.innerHTML = contacts.map(c => `
      <div class="wa-automation-contact-item" data-phone="${c.phone}">
        <span>${c.name || c.phone}</span>
        <span style="color: #666; font-size: 12px;">${c.phone}</span>
      </div>
    `).join('');
    
    list.querySelectorAll('.wa-automation-contact-item').forEach(item => {
      item.addEventListener('click', () => {
        list.querySelectorAll('.wa-automation-contact-item').forEach(i => i.classList.remove('selected'));
        item.classList.add('selected');
      });
    });
  }

  /**
   * Send quick message
   */
  async function sendQuickMessage() {
    const message = document.getElementById('wa-custom-message').value;
    const selectedContact = document.querySelector('.wa-automation-contact-item.selected');
    
    if (!message) {
      showMessage('Please enter a message', 'error');
      return;
    }
    
    // Get current chat phone if no contact selected
    let phone = selectedContact?.dataset.phone;
    if (!phone) {
      phone = getCurrentChatPhone();
    }
    
    if (!phone) {
      showMessage('Please open a chat or select a contact', 'error');
      return;
    }
    
    try {
      // Try to send via WhatsApp UI
      const success = await sendViaWhatsApp(phone, message);
      
      if (success) {
        // Also save to backend
        await sendMessage({
          type: 'SAVE_CONTACT',
          data: { phone, name: '' }
        });
        
        showMessage('Message sent successfully!', 'success');
        
        // Clear form
        document.getElementById('wa-custom-message').value = '';
        document.getElementById('wa-template-select').value = '';
      } else {
        showMessage('Failed to send message', 'error');
      }
    } catch (error) {
      console.error('Send message error:', error);
      showMessage(error.message, 'error');
    }
  }

  /**
   * Get current chat phone number
   */
  function getCurrentChatPhone() {
    try {
      // Try to get phone from header
      const header = document.querySelector('[data-testid="conversation-info-header"]');
      if (header) {
        const phoneSpan = header.querySelector('span[title]');
        if (phoneSpan) {
          return phoneSpan.title.replace(/\D/g, '');
        }
      }
      
      // Try alternative method
      const chatName = document.querySelector('header div[contenteditable="true"]');
      if (chatName) {
        return chatName.textContent.replace(/\D/g, '');
      }
      
      return null;
    } catch (e) {
      console.error('Error getting phone:', e);
      return null;
    }
  }

  /**
   * Send message via WhatsApp UI
   */
  async function sendViaWhatsApp(phone, message) {
    try {
      // Find message input
      const input = document.querySelector('[data-testid="conversation-compose-box-input"]');
      if (!input) {
        console.error('Message input not found');
        return false;
      }
      
      // Set message
      input.textContent = message;
      input.dispatchEvent(new Event('input', { bubbles: true }));
      
      // Wait a bit
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Find send button
      const sendButton = document.querySelector('[data-testid="send-button"]');
      if (!sendButton) {
        console.error('Send button not found');
        return false;
      }
      
      // Click send
      sendButton.click();
      
      return true;
    } catch (error) {
      console.error('Send via WhatsApp error:', error);
      return false;
    }
  }

  /**
   * Show message
   */
  function showMessage(text, type) {
    const content = document.querySelector('.wa-automation-panel-content');
    const existing = content.querySelector('.wa-automation-message');
    if (existing) existing.remove();
    
    const msg = document.createElement('div');
    msg.className = `wa-automation-message ${type}`;
    msg.textContent = text;
    
    content.insertBefore(msg, content.firstChild);
    
    // Remove after 3 seconds
    setTimeout(() => msg.remove(), 3000);
  }

  /**
   * Set up observers
   */
  function setupObservers() {
    // Observe URL changes for chat switching
    let lastUrl = location.href;
    new MutationObserver(() => {
      const url = location.href;
      if (url !== lastUrl) {
        lastUrl = url;
        onChatChange();
      }
    }).observe(document, { subtree: true, childList: true });
    
    // Also poll for chat changes
    setInterval(onChatChange, 2000);
  }

  /**
   * On chat change
   */
  function onChatChange() {
    const phone = getCurrentChatPhone();
    if (phone && phone !== currentChatPhone) {
      currentChatPhone = phone;
      console.log('Chat changed to:', phone);
      
      // Could show contact info or auto-reply options here
    }
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
