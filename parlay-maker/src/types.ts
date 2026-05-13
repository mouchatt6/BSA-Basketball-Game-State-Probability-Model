export type StatType = "points" | "rebounds" | "assists" | "threes" | "steals" | "blocks";

export interface PlayerProp {
  stat: StatType;
  line: number;
  direction: "over" | "under";
  odds: number; // American odds e.g. -110
}

export interface Player {
  id: string;
  name: string;
  team: string;
  teamColor: string;
  position: string;
  props: Record<StatType, { line: number; avgOdds: number }>;
}

export interface ParlayLeg {
  player: Player;
  prop: PlayerProp;
}

export interface Game {
  id: string;
  homeTeam: string;
  awayTeam: string;
  homeColor: string;
  awayColor: string;
  time: string;
  spread: number; // home spread
}
