// Badges simplifiés des moyens de paiement (indicateurs fonctionnels, aux
// couleurs des marques). Rendu vectoriel léger, sans dépendance d'assets.

export function WaveLogo({ height = 26 }: { height?: number }) {
  return (
    <svg viewBox="0 0 96 40" height={height} role="img" aria-label="Wave">
      <rect x="0" y="0" width="40" height="40" rx="20" fill="#1DC3F0" />
      <path
        d="M9 24c3 0 3-5 6-5s3 5 6 5 3-5 6-5 3 5 6 5"
        fill="none"
        stroke="#fff"
        strokeWidth="2.6"
        strokeLinecap="round"
      />
      <text
        x="48"
        y="27"
        fontFamily="Inter, system-ui, sans-serif"
        fontSize="20"
        fontWeight="800"
        fill="#1DC3F0"
      >
        wave
      </text>
    </svg>
  );
}

export function CardsLogo({ height = 26 }: { height?: number }) {
  return (
    <svg viewBox="0 0 96 40" height={height} role="img" aria-label="Visa / Mastercard">
      <text
        x="2"
        y="26"
        fontFamily="Arial, sans-serif"
        fontSize="17"
        fontStyle="italic"
        fontWeight="800"
        fill="#1A1F71"
      >
        VISA
      </text>
      <circle cx="64" cy="20" r="11" fill="#EB001B" />
      <circle cx="78" cy="20" r="11" fill="#F79E1B" opacity="0.9" />
    </svg>
  );
}

export function OrangeMoneyLogo({ height = 26 }: { height?: number }) {
  return (
    <svg viewBox="0 0 120 40" height={height} role="img" aria-label="Orange Money">
      {/* Deux flèches : noire (haut-droite) + orange (bas-gauche) */}
      <g strokeWidth="5" strokeLinecap="round" strokeLinejoin="round" fill="none">
        <path d="M8 26 L22 12 M22 12 H13 M22 12 V21" stroke="#000" />
        <path d="M34 14 L20 28 M20 28 H29 M20 28 V19" stroke="#FF7900" />
      </g>
      <text
        x="44"
        y="20"
        fontFamily="Inter, system-ui, sans-serif"
        fontSize="12"
        fontWeight="800"
        fill="#FF7900"
      >
        Orange
      </text>
      <text
        x="44"
        y="33"
        fontFamily="Inter, system-ui, sans-serif"
        fontSize="11"
        fontWeight="600"
        fill="#e5e7eb"
      >
        Money
      </text>
    </svg>
  );
}
