export function americanToDecimal(odds: number): number {
  if (odds > 0) return odds / 100 + 1;
  return 100 / Math.abs(odds) + 1;
}

export function oddsToImpliedProb(odds: number): number {
  const dec = americanToDecimal(odds);
  return 1 / dec;
}

export function calcParlayOdds(legs: number[]): number {
  // legs are american odds, returns american odds for parlay
  const decimal = legs.reduce((acc, o) => acc * americanToDecimal(o), 1);
  if (decimal >= 2) return Math.round((decimal - 1) * 100);
  return Math.round(-100 / (decimal - 1));
}

export function calcPayout(stake: number, odds: number): number {
  if (odds > 0) return stake + (stake * odds) / 100;
  return stake + (stake * 100) / Math.abs(odds);
}

export function formatOdds(odds: number): string {
  return odds > 0 ? `+${odds}` : `${odds}`;
}
