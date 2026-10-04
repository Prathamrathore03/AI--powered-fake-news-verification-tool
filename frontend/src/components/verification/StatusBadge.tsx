import React from 'react';
import {
  CheckCircleIcon,
  XCircleIcon,
  AlertTriangleIcon,
  HelpCircleIcon,
  AlertCircleIcon,
} from '../common/Icons';

interface StatusBadgeProps {
  status?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  if (!status) return null;

  const normalized = status.trim().toLowerCase();

  let badgeVariant = 'status-variant-neutral';
  let Icon = HelpCircleIcon;
  let displayLabel = status.toUpperCase();

  if (
    normalized.includes('support') ||
    normalized === 'true' ||
    normalized === 'verified' ||
    normalized === 'corroborated'
  ) {
    badgeVariant = 'status-variant-supported';
    Icon = CheckCircleIcon;
    displayLabel = 'SUPPORTED // CORROBORATED';
  } else if (
    normalized.includes('contradict') ||
    normalized === 'false' ||
    normalized === 'debunked' ||
    normalized === 'fake' ||
    normalized === 'refuted'
  ) {
    badgeVariant = 'status-variant-contradicted';
    Icon = XCircleIcon;
    displayLabel = 'CONTRADICTED // REFUTED';
  } else if (
    normalized.includes('mix') ||
    normalized.includes('mislead') ||
    normalized.includes('partial')
  ) {
    badgeVariant = 'status-variant-mixed';
    Icon = AlertTriangleIcon;
    displayLabel = 'MIXED // CONFLICTING EVIDENCE';
  } else if (
    normalized.includes('insufficient') ||
    normalized.includes('inconclusive') ||
    normalized.includes('unverified')
  ) {
    badgeVariant = 'status-variant-insufficient';
    Icon = HelpCircleIcon;
    displayLabel = 'INSUFFICIENT EVIDENCE';
  } else if (normalized.includes('error') || normalized.includes('fail')) {
    badgeVariant = 'status-variant-error';
    Icon = AlertCircleIcon;
    displayLabel = 'VERIFICATION ERROR';
  }

  return (
    <div className={`tactical-status-badge ${badgeVariant} badge-size-${size}`}>
      <span className="status-beacon" aria-hidden="true" />
      <Icon size={size === 'lg' ? 18 : 14} className="status-icon" />
      <span className="status-text">{displayLabel}</span>
    </div>
  );
};
