import type { SVGProps } from "react";

export type IconName =
  | "rice"
  | "wheat"
  | "maize"
  | "pulse"
  | "mustard"
  | "vegetables"
  | "jute"
  | "other"
  | "rain"
  | "irrigation"
  | "both"
  | "drainage"
  | "standingWater"
  | "mixed"
  | "unknown"
  | "check"
  | "close"
  | "water"
  | "soil"
  | "stability";

type Props = SVGProps<SVGSVGElement> & { name: IconName };

export default function FieldIcon({ name, ...props }: Props) {
  const common = {
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.7,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
  };

  const shapes: Record<IconName, JSX.Element> = {
    rice: <><path d="M7 21V9c0-3 2-5 5-6v18" /><path d="M12 7c3 0 5 2 5 5M12 11c-3 0-5 2-5 5M12 15c3 0 5 2 5 5" /></>,
    wheat: <><path d="M12 22V3" /><path d="M12 6 8 4M12 9 16 6M12 12 8 9M12 15 16 12M12 18 8 15" /></>,
    maize: <><path d="M9 20c-2-4-2-10 3-15 5 5 5 11 3 15Z" /><path d="M12 7v11M9 10h6M9 14h6" /></>,
    pulse: <><path d="M5 17c3-7 8-10 14-10-1 6-4 11-11 12Z" /><circle cx="11" cy="13" r="1" /><circle cx="15" cy="10" r="1" /></>,
    mustard: <><path d="M12 22V10" /><path d="M12 13 7 9M12 15l5-5" /><circle cx="7" cy="7" r="2" /><circle cx="17" cy="8" r="2" /><circle cx="12" cy="5" r="2" /></>,
    vegetables: <><path d="M6 10c0 7 2 10 6 10s6-3 6-10Z" /><path d="M9 10c-1-3 0-5 3-7 3 2 4 4 3 7M12 10V4" /></>,
    jute: <><path d="M12 22V3" /><path d="M12 7c-4 0-6 2-6 5 4 0 6-2 6-5ZM12 12c4 0 6 2 6 5-4 0-6-2-6-5Z" /></>,
    other: <><circle cx="12" cy="12" r="7" /><path d="M12 9v6M9 12h6" /></>,
    rain: <><path d="M7 15h10a4 4 0 0 0 0-8 6 6 0 0 0-11-1A4.5 4.5 0 0 0 7 15Z" /><path d="m8 18-1 3M12 18l-1 3M16 18l-1 3" /></>,
    irrigation: <><path d="M4 16h16M7 16v4M17 16v4" /><path d="M7 12c3-4 7-4 10 0" /><path d="M12 7c0 2-2 3-2 5h4c0-2-2-3-2-5Z" /></>,
    both: <><path d="M4 15h7a3 3 0 0 0 0-6 5 5 0 0 0-9 1" /><path d="M14 15h6M17 12v6" /><path d="m6 18-1 3M10 18l-1 3" /></>,
    drainage: <><path d="M4 6h16v5H4Z" /><path d="M7 14l3 3 7-7M12 11v8" /></>,
    standingWater: <><path d="M4 8h16v10H4Z" /><path d="M6 13c2-1 4-1 6 0s4 1 6 0M6 16c2-1 4-1 6 0s4 1 6 0" /></>,
    mixed: <><path d="M5 8h10l-2-2M15 8l-2 2M19 16H9l2-2M9 16l2 2" /></>,
    unknown: <><circle cx="12" cy="12" r="9" /><path d="M9.8 9a2.4 2.4 0 1 1 4 1.8c-1.1.8-1.8 1.2-1.8 2.7M12 17h.01" /></>,
    check: <><circle cx="12" cy="12" r="9" /><path d="m8 12 2.5 2.5L16.5 9" /></>,
    close: <><circle cx="12" cy="12" r="9" /><path d="m9 9 6 6M15 9l-6 6" /></>,
    water: <><path d="M12 3c4 5 6 8 6 11a6 6 0 0 1-12 0c0-3 2-6 6-11Z" /><path d="M9 15c.7 1.3 1.7 2 3 2" /></>,
    soil: <><path d="M4 9c3-2 6-2 8 0 2-2 5-2 8 0v9H4Z" /><path d="M4 13h16M8 13v5M15 13v5" /></>,
    stability: <><path d="M4 17h16M6 14l4-4 3 3 5-6" /><path d="M18 7v4h-4" /></>,
  };

  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false" {...common} {...props}>
      {shapes[name]}
    </svg>
  );
}
