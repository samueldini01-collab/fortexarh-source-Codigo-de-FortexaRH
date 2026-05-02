/**
 * CountryFlag — cross-platform flag renderer.
 *
 * Uses country-flag-icons (SVG) so flags render consistently on Windows,
 * macOS, Linux, Android and iOS — unlike native Unicode regional-indicator
 * emoji which Windows fonts do not support.
 *
 * Usage:
 *   <CountryFlag code="US" className="w-5 h-auto" />
 */
import PropTypes from "prop-types";
import * as Flags from "country-flag-icons/react/3x2";

export default function CountryFlag({ code, className = "inline-block w-5 h-auto align-middle mr-1", title }) {
  const normalized = (code || "").toUpperCase();
  const FlagComponent = Flags[normalized];
  if (!FlagComponent) {
    return (
      <span
        className={`inline-block text-xs font-bold text-slate-600 bg-slate-100 rounded px-1 ${className}`}
        title={title || normalized}
        data-testid={`flag-${normalized.toLowerCase()}-fallback`}
      >
        {normalized || "??"}
      </span>
    );
  }
  return (
    <FlagComponent
      className={className}
      title={title || normalized}
      data-testid={`flag-${normalized.toLowerCase()}`}
    />
  );
}

CountryFlag.propTypes = {
  code: PropTypes.string.isRequired,
  className: PropTypes.string,
  title: PropTypes.string,
};
