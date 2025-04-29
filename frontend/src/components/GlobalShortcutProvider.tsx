import React, { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import KeyboardShortcuts from './KeyboardShortcuts';

interface GlobalShortcutProviderProps {
  children: React.ReactNode;
}

const GlobalShortcutProvider: React.FC<GlobalShortcutProviderProps> = ({ children }) => {
  const navigate = useNavigate();

  const goToDashboard = useCallback(() => navigate('/dashboard'), [navigate]);
  const goToConvert = useCallback(() => navigate('/convert'), [navigate]);
  const goToBatchConvert = useCallback(() => navigate('/batch-convert'), [navigate]);
  const goToHistory = useCallback(() => navigate('/history'), [navigate]);
  const goToTemplates = useCallback(() => navigate('/templates'), [navigate]);
  const goToSettings = useCallback(() => navigate('/settings'), [navigate]);

  const shortcuts = [
    // Navigation shortcuts
    {
      key: 'd',
      description: 'Go to Dashboard',
      action: goToDashboard,
      altKey: true,
      scope: 'Navigation',
    },
    {
      key: 'c',
      description: 'Go to Convert',
      action: goToConvert,
      altKey: true,
      scope: 'Navigation',
    },
    {
      key: 'b',
      description: 'Go to Batch Convert',
      action: goToBatchConvert,
      altKey: true,
      scope: 'Navigation',
    },
    {
      key: 'h',
      description: 'Go to History',
      action: goToHistory,
      altKey: true,
      scope: 'Navigation',
    },
    {
      key: 't',
      description: 'Go to Templates',
      action: goToTemplates,
      altKey: true,
      scope: 'Navigation',
    },
    {
      key: 's',
      description: 'Go to Settings',
      action: goToSettings,
      altKey: true,
      scope: 'Navigation',
    },
    
    // Theme toggle
    {
      key: 'd',
      description: 'Toggle dark mode',
      action: () => {
        document.documentElement.classList.toggle('dark');
        const isDark = document.documentElement.classList.contains('dark');
        localStorage.setItem('darkMode', isDark ? 'true' : 'false');
      },
      ctrlKey: true,
      altKey: true,
      scope: 'Appearance',
    },
    
    // File operations
    {
      key: 'n',
      description: 'New conversion',
      action: goToConvert,
      ctrlKey: true,
      scope: 'File',
    },
    
    // Help
    {
      key: '/',
      description: 'Search',
      action: () => {
        const searchInput = document.querySelector('input[type="search"]') as HTMLInputElement;
        if (searchInput) {
          searchInput.focus();
        }
      },
      ctrlKey: true,
      scope: 'Help',
    },
    
    // Accessibility
    {
      key: '1',
      description: 'Increase font size',
      action: () => {
        const currentSize = parseFloat(getComputedStyle(document.documentElement).fontSize);
        document.documentElement.style.fontSize = `${currentSize + 1}px`;
      },
      ctrlKey: true,
      altKey: true,
      scope: 'Accessibility',
    },
    {
      key: '2',
      description: 'Decrease font size',
      action: () => {
        const currentSize = parseFloat(getComputedStyle(document.documentElement).fontSize);
        document.documentElement.style.fontSize = `${currentSize - 1}px`;
      },
      ctrlKey: true,
      altKey: true,
      scope: 'Accessibility',
    },
    {
      key: '0',
      description: 'Reset font size',
      action: () => {
        document.documentElement.style.fontSize = '';
      },
      ctrlKey: true,
      altKey: true,
      scope: 'Accessibility',
    },
  ];

  return <KeyboardShortcuts shortcuts={shortcuts}>{children}</KeyboardShortcuts>;
};

export default GlobalShortcutProvider; 