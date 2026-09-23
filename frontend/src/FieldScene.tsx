import { useRef, type CSSProperties, type PointerEvent } from "react";

type TiltStyle = CSSProperties & { "--tilt-x"?: string; "--tilt-y"?: string };

/**
 * An original CSS-3D art direction for BoponX; it is not NASA imagery,
 * a geographic model, a measured farm, or a satellite-derived field map.
 * No WebGL/library/network dependency. Reduced motion is respected in CSS.
 */
export default function FieldScene() {
  const sceneRef = useRef<HTMLDivElement>(null);

  function trackPointer(event: PointerEvent<HTMLDivElement>) {
    if (event.pointerType !== "mouse" || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const frame = sceneRef.current;
    if (!frame) return;
    const rect = frame.getBoundingClientRect();
    const dx = (event.clientX - rect.left) / rect.width - 0.5;
    const dy = (event.clientY - rect.top) / rect.height - 0.5;
    frame.style.setProperty("--tilt-x", `${(-dy * 7).toFixed(2)}deg`);
    frame.style.setProperty("--tilt-y", `${(dx * 9).toFixed(2)}deg`);
  }

  function resetTilt() {
    sceneRef.current?.style.setProperty("--tilt-x", "0deg");
    sceneRef.current?.style.setProperty("--tilt-y", "0deg");
  }

  const defaultTilt: TiltStyle = { "--tilt-x": "0deg", "--tilt-y": "0deg" };

  return (
    <figure className="field-scene" aria-label="Illustrative 3D scene of paddy fields, a winding river, a red sun and a satellite; not a geographic or NASA measurement">
      <div className="field-scene__stage" ref={sceneRef} style={defaultTilt} onPointerMove={trackPointer} onPointerLeave={resetTilt} aria-hidden="true">
        <div className="field-scene__orbit orbit-1" />
        <div className="field-scene__orbit orbit-2" />
        <div className="field-scene__halo" />
        <div className="field-scene__sun" />
        <div className="field-scene__satellite">
          <i className="solar-wing" /><i className="sat-body" /><i className="solar-wing" />
        </div>
        <div className="field-scene__world">
          <div className="field-scene__earth">
            <div className="field-scene__river river-1" />
            <div className="field-scene__river river-2" />
            <div className="field-scene__plots">
              {Array.from({ length: 16 }).map((_, index) => (
                <span className={`field-plot field-plot--${index % 4}`} key={index}>
                  <i />
                </span>
              ))}
            </div>
            <div className="field-scene__river river-3" />
          </div>
        </div>
        <div className="field-scene__beacon beacon-1" />
        <div className="field-scene__beacon beacon-2" />
      </div>
      <figcaption className="field-scene__caption">
        <strong>EARTH / FIELD VIEW <span>01—03</span></strong>
        <span>Conceptual 3D artwork <i lang="bn">· ধারণাগত ত্রিমাত্রিক চিত্র</i></span>
      </figcaption>
    </figure>
  );
}
