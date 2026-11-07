import { useState } from 'react';
import { UNITS_CONFIG } from '../lib/game';

export interface UnitAvatarProps {
  unitId: string;
  className?: string;
  alt?: string;
}

export function UnitAvatar({ unitId, className = '', alt }: UnitAvatarProps) {
  const [errorUnitId, setErrorUnitId] = useState<string | null>(null);
  const config = UNITS_CONFIG[unitId];

  if (!config) {
    return <span className={className}>🐾</span>;
  }

  const hasError = errorUnitId === unitId;

  if (!config.image || hasError) {
    return (
      <span className={className} role="img" aria-label={config.name}>
        {config.sprite}
      </span>
    );
  }

  return (
    <img
      src={config.image}
      alt={alt || config.name}
      className={className}
      onError={(e) => {
        e.currentTarget.style.display = 'none';
        setErrorUnitId(unitId);
      }}
    />
  );
}

export default UnitAvatar;
