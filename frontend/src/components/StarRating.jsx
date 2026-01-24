import React from 'react';
import { Star } from 'lucide-react';

/**
 * Interactive star rating component.
 *
 * @param {number} value - Current rating (1-5)
 * @param {function} onChange - Callback when rating changes
 * @param {boolean} readOnly - If true, disables interaction
 * @param {string} size - Size of stars ('sm', 'md', 'lg')
 */
export default function StarRating({
  value = 0,
  onChange,
  readOnly = false,
  size = 'md'
}) {
  const [hoverValue, setHoverValue] = React.useState(0);

  const sizeClasses = {
    sm: 16,
    md: 24,
    lg: 32,
  };

  const starSize = sizeClasses[size] || sizeClasses.md;

  const handleClick = (rating) => {
    if (!readOnly && onChange) {
      onChange(rating);
    }
  };

  const handleMouseEnter = (rating) => {
    if (!readOnly) {
      setHoverValue(rating);
    }
  };

  const handleMouseLeave = () => {
    setHoverValue(0);
  };

  const displayValue = hoverValue || value;

  return (
    <div
      className="flex gap-1"
      onMouseLeave={handleMouseLeave}
    >
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          onClick={() => handleClick(star)}
          onMouseEnter={() => handleMouseEnter(star)}
          disabled={readOnly}
          className={`transition-colors ${
            readOnly ? 'cursor-default' : 'cursor-pointer hover:scale-110'
          }`}
          aria-label={`Rate ${star} stars`}
        >
          <Star
            size={starSize}
            className={`transition-colors ${
              star <= displayValue
                ? 'fill-yellow-400 text-yellow-400'
                : 'fill-none text-gray-300'
            }`}
          />
        </button>
      ))}
    </div>
  );
}
