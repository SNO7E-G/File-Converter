import React, { useEffect, useState } from 'react';
import { useError, ErrorNotification as ErrorNotificationType } from '../context/ErrorContext';

// Styles for the notification container
const containerStyles: React.CSSProperties = {
  position: 'fixed',
  top: '20px',
  right: '20px',
  zIndex: 9999,
  display: 'flex',
  flexDirection: 'column',
  gap: '10px',
  maxWidth: '400px',
  maxHeight: '80vh',
  overflowY: 'auto',
  padding: '10px',
};

// Styles for individual notification
const getNotificationStyles = (severity: ErrorNotificationType['severity']): React.CSSProperties => {
  const baseStyles: React.CSSProperties = {
    padding: '12px 16px',
    borderRadius: '4px',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
    display: 'flex',
    flexDirection: 'column',
    position: 'relative',
    animation: 'slideIn 0.3s ease-out',
    transition: 'opacity 0.3s ease-out, transform 0.3s ease-out',
    maxWidth: '100%',
  };

  // Color variations based on severity
  switch (severity) {
    case 'error':
      return {
        ...baseStyles,
        backgroundColor: '#FEF2F2',
        borderLeft: '4px solid #DC2626',
        color: '#991B1B',
      };
    case 'warning':
      return {
        ...baseStyles,
        backgroundColor: '#FFFBEB',
        borderLeft: '4px solid #F59E0B',
        color: '#92400E',
      };
    case 'info':
      return {
        ...baseStyles,
        backgroundColor: '#EFF6FF',
        borderLeft: '4px solid #3B82F6',
        color: '#1E40AF',
      };
    case 'success':
      return {
        ...baseStyles,
        backgroundColor: '#ECFDF5',
        borderLeft: '4px solid #10B981',
        color: '#065F46',
      };
    default:
      return baseStyles;
  }
};

// Close button styles
const closeButtonStyles: React.CSSProperties = {
  position: 'absolute',
  top: '8px',
  right: '8px',
  background: 'transparent',
  border: 'none',
  cursor: 'pointer',
  fontSize: '16px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  width: '24px',
  height: '24px',
  borderRadius: '50%',
  color: '#666',
};

// Message styles
const messageStyles: React.CSSProperties = {
  marginBottom: '4px',
  fontWeight: 600,
  paddingRight: '20px',
};

// Details styles
const detailsStyles: React.CSSProperties = {
  fontSize: '14px',
  opacity: 0.9,
};

// Progress bar styles
const progressBarContainerStyles: React.CSSProperties = {
  width: '100%',
  height: '4px',
  backgroundColor: 'rgba(0, 0, 0, 0.1)',
  borderRadius: '2px',
  marginTop: '8px',
  overflow: 'hidden',
};

interface ProgressBarProps {
  duration: number;
  onComplete: () => void;
}

// Progress bar component for auto-dismiss countdown
const ProgressBar: React.FC<ProgressBarProps> = ({ duration, onComplete }) => {
  const [width, setWidth] = useState(100);

  useEffect(() => {
    const interval = setInterval(() => {
      setWidth((prevWidth) => {
        const newWidth = prevWidth - (100 / (duration / 100));
        if (newWidth <= 0) {
          clearInterval(interval);
          onComplete();
          return 0;
        }
        return newWidth;
      });
    }, 100);

    return () => clearInterval(interval);
  }, [duration, onComplete]);

  return (
    <div style={progressBarContainerStyles}>
      <div
        style={{
          height: '100%',
          width: `${width}%`,
          backgroundColor: 'rgba(0, 0, 0, 0.2)',
          transition: 'width 0.1s linear',
        }}
      />
    </div>
  );
};

// Individual notification component
const NotificationItem: React.FC<{
  notification: ErrorNotificationType;
  onClose: () => void;
}> = ({ notification, onClose }) => {
  const [isClosing, setIsClosing] = useState(false);

  const handleClose = () => {
    setIsClosing(true);
    setTimeout(() => {
      onClose();
    }, 300);
  };

  return (
    <div
      style={{
        ...getNotificationStyles(notification.severity),
        opacity: isClosing ? 0 : 1,
        transform: isClosing ? 'translateX(10px)' : 'translateX(0)',
      }}
    >
      <button style={closeButtonStyles} onClick={handleClose}>
        ×
      </button>
      <div style={messageStyles}>{notification.message}</div>
      {notification.details && <div style={detailsStyles}>{notification.details}</div>}
      {notification.autoDismiss && notification.dismissAfter && (
        <ProgressBar duration={notification.dismissAfter} onComplete={handleClose} />
      )}
    </div>
  );
};

// Main component that displays all notifications
const ErrorNotification: React.FC = () => {
  const { errors, removeError } = useError();

  if (errors.length === 0) {
    return null;
  }

  return (
    <div style={containerStyles}>
      {errors.map((notification) => (
        <NotificationItem
          key={notification.id}
          notification={notification}
          onClose={() => removeError(notification.id)}
        />
      ))}
    </div>
  );
};

export default ErrorNotification; 