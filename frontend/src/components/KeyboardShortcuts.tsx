import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';

interface Shortcut {
  key: string;
  description: string;
  action: () => void;
  ctrlKey?: boolean;
  altKey?: boolean;
  shiftKey?: boolean;
  metaKey?: boolean;
  scope?: string;
  disabled?: boolean;
}

interface KeyboardShortcutsProps {
  shortcuts: Shortcut[];
  children?: React.ReactNode;
}

const KeyboardShortcuts: React.FC<KeyboardShortcutsProps> = ({ shortcuts, children }) => {
  const [showHelp, setShowHelp] = useState(false);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Toggle help dialog with ? key
      if (event.key === '?' && !event.ctrlKey && !event.altKey && !event.metaKey) {
        setShowHelp(prev => !prev);
        event.preventDefault();
        return;
      }

      // Check if esc key is pressed to close help dialog
      if (event.key === 'Escape' && showHelp) {
        setShowHelp(false);
        event.preventDefault();
        return;
      }

      // Handle other shortcuts
      for (const shortcut of shortcuts) {
        if (shortcut.disabled) continue;

        const ctrlMatch = shortcut.ctrlKey === undefined || shortcut.ctrlKey === event.ctrlKey;
        const altMatch = shortcut.altKey === undefined || shortcut.altKey === event.altKey;
        const shiftMatch = shortcut.shiftKey === undefined || shortcut.shiftKey === event.shiftKey;
        const metaMatch = shortcut.metaKey === undefined || shortcut.metaKey === event.metaKey;
        const keyMatch = shortcut.key.toLowerCase() === event.key.toLowerCase();

        if (ctrlMatch && altMatch && shiftMatch && metaMatch && keyMatch) {
          shortcut.action();
          event.preventDefault();
          break;
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [shortcuts, showHelp]);

  // Group shortcuts by scope
  const shortcutsByScope = shortcuts.reduce<Record<string, Shortcut[]>>((acc, shortcut) => {
    const scope = shortcut.scope || 'General';
    if (!acc[scope]) {
      acc[scope] = [];
    }
    acc[scope].push(shortcut);
    return acc;
  }, {});

  const formatShortcut = (shortcut: Shortcut): string => {
    const parts: string[] = [];
    if (shortcut.ctrlKey) parts.push('Ctrl');
    if (shortcut.altKey) parts.push('Alt');
    if (shortcut.shiftKey) parts.push('Shift');
    if (shortcut.metaKey) parts.push('Meta');
    parts.push(shortcut.key.toUpperCase());
    return parts.join(' + ');
  };

  const ShortcutsHelpDialog = () => (
    <div className="modal-backdrop" onClick={() => setShowHelp(false)}>
      <div 
        className="modal-content p-6 max-w-2xl max-h-[80vh] overflow-auto" 
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Keyboard Shortcuts</h2>
          <button 
            onClick={() => setShowHelp(false)} 
            className="p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
            aria-label="Close keyboard shortcuts dialog"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        </div>
        
        <div className="space-y-6">
          <div className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Press <span className="kbd">?</span> anytime to show this help dialog
          </div>
          
          {Object.entries(shortcutsByScope).map(([scope, scopeShortcuts]) => (
            <div key={scope}>
              <h3 className="text-lg font-medium mb-2">{scope}</h3>
              <div className="bg-gray-50 dark:bg-gray-800 rounded-lg overflow-hidden">
                <table className="w-full">
                  <tbody>
                    {scopeShortcuts.map((shortcut, index) => (
                      <tr 
                        key={index} 
                        className={`border-b border-gray-200 dark:border-gray-700 ${
                          shortcut.disabled ? 'opacity-50' : ''
                        }`}
                      >
                        <td className="py-2 px-4 w-1/3">
                          <span className="kbd">{formatShortcut(shortcut)}</span>
                        </td>
                        <td className="py-2 px-4 w-2/3">
                          {shortcut.description}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </div>
        
        <div className="mt-6 text-sm text-gray-500 dark:text-gray-400">
          Tip: Most shortcuts can be customized in your user settings.
        </div>
      </div>
    </div>
  );

  return (
    <>
      {children}
      {showHelp && createPortal(<ShortcutsHelpDialog />, document.body)}
    </>
  );
};

export default KeyboardShortcuts; 