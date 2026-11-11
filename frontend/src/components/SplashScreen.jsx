import { useEffect, useState } from "react";
import Logo from "./Logo";

const BRAND = "ludex";

export default function SplashScreen({ onComplete }) {
  const [visibleLetters, setVisibleLetters] = useState(0);
  const [finished, setFinished] = useState(false);

  useEffect(() => {
    const reducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    ).matches;

    if (reducedMotion) {
      onComplete();
      return;
    }

    const timers = [];

    BRAND.split("").forEach((_, index) => {
      timers.push(
        setTimeout(() => {
          setVisibleLetters(index + 1);
        }, 1500 + index * 140)
      );
    });

    timers.push(setTimeout(() => setFinished(true), 2600));
    timers.push(setTimeout(onComplete, 3200));

    return () => timers.forEach(clearTimeout);
  }, [onComplete]);

  return (
    <div
      className={`splash-screen ${finished ? "splash-screen--exit" : ""}`}
    >
      <Logo text={BRAND.slice(0, visibleLetters)} className="splash-logo" />
    </div>
  );
}